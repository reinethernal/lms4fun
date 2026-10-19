"""Interactive Telegram bot handlers (python-telegram-bot)."""
from __future__ import annotations

import logging
from typing import Any

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from telegram.request import HTTPXRequest

from apps.submissions.models import Submission

from .config import get_telegram_config
from .formatting import (
    comment_choice_keyboard,
    format_submission_card,
    review_keyboard,
)
from .services import (
    get_account_by_chat,
    link_account,
    open_submission_for_user,
    recheck_via_bot,
    review_via_bot,
    unlink_account,
    format_pending_message,
)

logger = logging.getLogger('apps.telegram')

WAITING_COMMENT = 1


def build_application() -> Application:
    cfg = get_telegram_config()
    if not cfg.is_ready:
        raise RuntimeError('Telegram-бот выключен или токен не задан в админ-панели')

    proxy_url = cfg.http_proxy or None
    request_kwargs: dict[str, Any] = {
        'connect_timeout': 20,
        'read_timeout': 30,
    }
    if proxy_url:
        request_kwargs['proxy'] = proxy_url

    request = HTTPXRequest(**request_kwargs)
    get_updates_request = HTTPXRequest(**request_kwargs)

    app = (
        Application.builder()
        .token(cfg.bot_token)
        .request(request)
        .get_updates_request(get_updates_request)
        .build()
    )

    comment_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(on_callback, pattern=r'^rv:\d+:comment$')],
        states={
            WAITING_COMMENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, on_comment_text),
                CallbackQueryHandler(on_callback, pattern=r'^rv:\d+:(accept_c|reject_c|cancel)$'),
            ],
        },
        fallbacks=[
            CommandHandler('cancel', cmd_cancel),
            CallbackQueryHandler(on_callback, pattern=r'^rv:\d+:cancel$'),
        ],
        allow_reentry=True,
        name='comment_flow',
        persistent=False,
    )

    app.add_handler(CommandHandler('start', cmd_start))
    app.add_handler(CommandHandler('help', cmd_help))
    app.add_handler(CommandHandler('pending', cmd_pending))
    app.add_handler(CommandHandler('unlink', cmd_unlink))
    app.add_handler(CommandHandler('status', cmd_status))
    app.add_handler(CommandHandler('cancel', cmd_cancel))
    app.add_handler(comment_conv)
    app.add_handler(CallbackQueryHandler(on_callback, pattern=r'^rv:\d+:'))
    return app


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or not update.message:
        return
    args = context.args or []
    chat_id = update.effective_chat.id
    username = update.effective_user.username if update.effective_user else ''

    if args:
        code = args[0]
        try:
            account = await _to_thread(link_account, code, chat_id, username or '')
        except ValueError as exc:
            await update.message.reply_text(str(exc))
            return
        await update.message.reply_text(
            f'Привязано к аккаунту {account.user.username}.\n'
            'Команды: /pending — решения на проверке, /help — справка.'
        )
        return

    account = await _to_thread(get_account_by_chat, chat_id)
    if account:
        await update.message.reply_text(
            f'Вы уже привязаны как {account.user.username}.\n'
            'Откройте /pending или /help.'
        )
        return

    await update.message.reply_text(
        'Бот для преподавателей CodeLearn.\n\n'
        '1. В админке платформы создайте код привязки.\n'
        '2. Отправьте сюда: /start КОД\n\n'
        'После привязки вы будете получать уведомления о решениях '
        'и сможете принимать / отклонять / комментировать их прямо в Telegram.'
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    await update.message.reply_text(
        'Команды:\n'
        '/start КОД — привязать аккаунт\n'
        '/pending — список решений на проверке\n'
        '/status — статус привязки\n'
        '/unlink — отвязать Telegram\n'
        '/cancel — отменить ввод комментария\n\n'
        'В карточке решения:\n'
        '✅ Принять / ❌ Отклонить\n'
        '💬 С комментарием — сначала текст, потом решение\n'
        '📄 Показать код / 🔄 Перепроверить'
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_chat:
        return
    account = await _to_thread(get_account_by_chat, update.effective_chat.id)
    if not account:
        await update.message.reply_text('Аккаунт не привязан. Используйте /start КОД.')
        return
    await update.message.reply_text(
        f'Привязан: {account.user.username} ({account.user.get_role_display()})\n'
        f'Уведомления о ручной проверке: {"да" if account.notify_manual_review else "нет"}\n'
        f'Уведомления о всех решениях: {"да" if account.notify_new_submissions else "нет"}'
    )


async def cmd_unlink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_chat:
        return
    ok = await _to_thread(unlink_account, update.effective_chat.id)
    await update.message.reply_text('Telegram отвязан.' if ok else 'Привязка не найдена.')


async def cmd_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_chat:
        return
    account = await _to_thread(get_account_by_chat, update.effective_chat.id)
    if not account:
        await update.message.reply_text('Сначала привяжите аккаунт: /start КОД')
        return
    text, markup = await _to_thread(format_pending_message, account.user)
    await update.message.reply_html(text, reply_markup=markup)


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop('comment_submission_id', None)
    context.user_data.pop('pending_comment', None)
    if update.message:
        await update.message.reply_text('Отменено.')
    return ConversationHandler.END


async def on_comment_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return WAITING_COMMENT
    submission_id = context.user_data.get('comment_submission_id')
    if not submission_id:
        await update.message.reply_text('Нет активного решения. Откройте карточку снова.')
        return ConversationHandler.END
    comment = update.message.text.strip()
    if not comment:
        await update.message.reply_text('Комментарий пустой. Напишите текст или /cancel.')
        return WAITING_COMMENT
    context.user_data['pending_comment'] = comment
    await update.message.reply_text(
        f'Комментарий сохранён ({len(comment)} симв.). Выберите действие:',
        reply_markup=comment_choice_keyboard(submission_id),
    )
    return WAITING_COMMENT


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.data or not update.effective_chat:
        return ConversationHandler.END

    await query.answer()
    parts = query.data.split(':')
    if len(parts) != 3 or parts[0] != 'rv':
        return ConversationHandler.END

    try:
        submission_id = int(parts[1])
    except ValueError:
        return ConversationHandler.END
    action = parts[2]

    account = await _to_thread(get_account_by_chat, update.effective_chat.id)
    if not account:
        await query.edit_message_text('Аккаунт не привязан. /start КОД')
        return ConversationHandler.END

    user = account.user

    try:
        if action == 'open':
            submission = await _to_thread(open_submission_for_user, user, submission_id)
            await query.edit_message_text(
                format_submission_card(submission),
                parse_mode='HTML',
                reply_markup=review_keyboard(submission.id),
            )
            return ConversationHandler.END

        if action == 'code':
            submission = await _to_thread(open_submission_for_user, user, submission_id)
            await query.edit_message_text(
                format_submission_card(submission, include_code=True),
                parse_mode='HTML',
                reply_markup=review_keyboard(submission.id, with_code=True),
            )
            return ConversationHandler.END

        if action == 'hidecode':
            submission = await _to_thread(open_submission_for_user, user, submission_id)
            await query.edit_message_text(
                format_submission_card(submission, include_code=False),
                parse_mode='HTML',
                reply_markup=review_keyboard(submission.id, with_code=False),
            )
            return ConversationHandler.END

        if action == 'comment':
            context.user_data['comment_submission_id'] = submission_id
            context.user_data.pop('pending_comment', None)
            await query.edit_message_text(
                'Напишите комментарий для ученика одним сообщением.\n'
                'Затем выберите «Принять» или «Отклонить».\n'
                'Отмена: /cancel'
            )
            return WAITING_COMMENT

        if action == 'cancel':
            context.user_data.pop('comment_submission_id', None)
            context.user_data.pop('pending_comment', None)
            submission = await _to_thread(open_submission_for_user, user, submission_id)
            await query.edit_message_text(
                format_submission_card(submission),
                parse_mode='HTML',
                reply_markup=review_keyboard(submission.id),
            )
            return ConversationHandler.END

        if action in ('accept', 'reject', 'accept_c', 'reject_c'):
            status = (
                Submission.Status.ACCEPTED
                if action.startswith('accept')
                else Submission.Status.REJECTED
            )
            comment = ''
            if action.endswith('_c'):
                comment = context.user_data.pop('pending_comment', '') or ''
                context.user_data.pop('comment_submission_id', None)
                if not comment:
                    await query.edit_message_text('Комментарий не найден. Нажмите «С комментарием» снова.')
                    return ConversationHandler.END
            submission = await _to_thread(review_via_bot, user, submission_id, status, comment)
            await query.edit_message_text(
                '✅ Решение обновлено.\n\n' + format_submission_card(submission),
                parse_mode='HTML',
            )
            return ConversationHandler.END

        if action == 'recheck':
            submission = await _to_thread(recheck_via_bot, user, submission_id)
            await query.edit_message_text(
                '🔄 Отправлено на повторную проверку.\n\n' + format_submission_card(submission),
                parse_mode='HTML',
            )
            return ConversationHandler.END

    except ValueError as exc:
        await query.edit_message_text(f'Ошибка: {exc}')
        return ConversationHandler.END
    except Exception:
        logger.exception('Callback failed: %s', query.data)
        await query.edit_message_text('Внутренняя ошибка. Попробуйте позже.')
        return ConversationHandler.END

    return ConversationHandler.END


async def _to_thread(func, *args):
    import asyncio
    return await asyncio.to_thread(func, *args)
