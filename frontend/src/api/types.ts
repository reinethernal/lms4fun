export type UserRole = 'superadmin' | 'admin' | 'teacher' | 'student' | 'parent';

export interface User {
  id: number;
  username: string;
  email: string;
  display_name: string;
  role: UserRole;
  avatar: string;
  is_active: boolean;
  last_login: string | null;
  date_joined: string;
  children?: ChildUser[];
}

export interface ChildUser {
  id: number;
  username: string;
  email: string;
  display_name: string;
  is_active: boolean;
  last_login: string | null;
  date_joined: string;
}

export interface StaffParent {
  id: number;
  username: string;
  email: string;
  display_name: string;
  is_active: boolean;
  last_login: string | null;
  children: ChildUser[];
}

export interface ProgrammingLanguage {
  id: number;
  name: string;
  slug: string;
  judge0_language_id: number;
  version: string;
  default_time_limit: number;
  default_memory_limit: number;
  default_output_limit: number;
  starter_code: string;
  editor_mode: string;
  is_active: boolean;
}

export interface Course {
  id: number;
  title: string;
  slug: string;
  description: string;
  primary_language: ProgrammingLanguage | null;
  age_from: number | null;
  age_to: number | null;
  level: string;
  status: string;
  cover_image: string;
  visibility: string;
  version: string;
  settings_json?: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
}

export interface Lesson {
  id: number;
  course: number;
  number: number;
  title: string;
  slug: string;
  goal: string;
  max_xp: number;
  status: string;
  sort_order: number;
  is_locked?: boolean;
  is_completed?: boolean;
  is_in_review?: boolean;
  language?: number;
  theory_text?: string;
  simple_explanation?: string;
  practice_text?: string;
  mini_project_text?: string;
  summary_text?: string;
  badge?: number | null;
  version?: string;
  content_format?: string;
  assets_json?: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
}

export interface TaskTestCase {
  stdin?: string;
  expected_stdout?: string;
  pattern?: string;
  hidden?: boolean;
}

export interface AdminTask {
  id: number;
  lesson: number;
  language: number;
  slug: string;
  title: string;
  description: string;
  task_type: string;
  starter_code: string;
  solution_template: string;
  stdin: string;
  expected_stdout: string;
  expected_stderr: string;
  checker_type: string;
  checker_code: string;
  visible_tests_json: TaskTestCase[];
  hidden_tests_json: TaskTestCase[];
  checker_config_json: Record<string, unknown>;
  max_xp: number;
  difficulty: string;
  is_required: boolean;
  sort_order: number;
}

export interface Task {
  id: number;
  lesson: number;
  title: string;
  description: string;
  task_type: string;
  starter_code: string;
  max_xp: number;
  difficulty: string;
  is_required: boolean;
  sort_order: number;
  language?: number;
  requires_stdin?: boolean;
  stdin_hint?: string;
  visible_tests_preview?: TaskTestCase[];
  input_count?: number;
  visible_tests_json?: unknown;
  test_cases?: TestCase[];
}

export interface TestCase {
  id: number;
  stdin: string;
  expected_stdout: string;
  expected_stderr: string;
  is_hidden: boolean;
  sort_order: number;
}

export interface UserProgress {
  id: number;
  course: number;
  course_title: string;
  lesson: number | null;
  task: number | null;
  xp_earned: number;
  tasks_completed: number;
  lessons_completed: number;
  last_activity_at: string | null;
  progress_json: Record<string, unknown>;
}

export interface LeaderboardEntry {
  rank: number;
  user_id: number;
  username: string;
  display_name: string;
  avatar: string;
  total_xp: number;
  tasks_completed: number;
}

export interface AwardedBadge {
  id: number;
  title: string;
  description: string;
  icon_url: string;
  level: string;
}

export interface Badge {
  id: number;
  title: string;
  description: string;
  icon: string;
  icon_url: string;
  badge_type: string;
  level: string;
  condition_type: string;
  condition_key: string;
  condition_value: number | null;
  condition_params: Record<string, unknown>;
  language: number | null;
  course: number | null;
  is_active: boolean;
}

export interface UserBadge {
  id: number;
  badge: Badge;
  awarded_at: string;
  awarded_by?: { id: number; username: string; display_name: string } | null;
  source?: 'manual' | 'auto';
}

export interface ProfileStats {
  total_xp: number;
  tasks_completed: number;
  lessons_completed: number;
  badges_count: number;
  rank: number | null;
}

export interface ProfilePermissions {
  can_edit: boolean;
  can_manage_badges: boolean;
  can_view_submissions: boolean;
}

export interface SkillHighlights {
  total_xp?: number;
  tasks_completed?: number;
  lessons_completed?: number;
  code_runs_success?: number;
  bugs_fixed?: number;
  top_skills?: { name: string; level: number }[];
}

export interface StudentProfile {
  user: User;
  stats: ProfileStats;
  progress: UserProgress[];
  badges: UserBadge[];
  skill_highlights: SkillHighlights;
  recent_submissions: AdminSubmission[];
  permissions: ProfilePermissions;
}

export interface ProfileUpdatePayload {
  display_name?: string;
  avatar?: string;
  password?: string;
  password_confirm?: string;
  remove_avatar?: boolean;
}

export interface ErrorGuidance {
  error_type: string;
  title: string;
  summary: string;
  attention: string[];
  why?: string;
  line?: number;
  raw?: string;
}

export interface CodeRunResult {
  status: string;
  language: string;
  stdout: string;
  stderr: string;
  compile_output: string;
  execution_time: number | null;
  memory_used: number | null;
  new_badges?: AwardedBadge[];
  error_guidance?: ErrorGuidance;
  waiting_for_input?: boolean;
}

export interface SubmissionResult {
  id?: number;
  status: string;
  xp_awarded: number;
  message: string;
  new_badges?: AwardedBadge[];
  failed_test_index?: number | null;
  expected?: string;
  got?: string;
  is_hidden?: boolean;
  task?: number;
  language?: number;
  code?: string;
  stdout?: string;
  stderr?: string;
  compile_output?: string;
  score?: number;
  checker_result?: Record<string, unknown>;
  submitted_at?: string;
  checked_at?: string | null;
  teacher_comment?: string;
}

export interface AdminSubmission {
  id: number;
  user: { id: number; username: string; display_name: string };
  task: { id: number; title: string; lesson_title?: string };
  language: string;
  status: string;
  xp_awarded: number;
  submitted_at: string | null;
}

export interface AdminSubmissionDetail extends AdminSubmission {
  code: string;
  stdout: string;
  stderr: string;
  compile_output: string;
  score: number | null;
  checker_result: Record<string, unknown> | null;
  checked_at: string | null;
  checked_by: { id: number; username: string; display_name: string } | null;
  teacher_comment: string;
}

export interface Group {
  id: number;
  title: string;
  description: string;
  teacher: User | null;
  is_active: boolean;
  members: User[];
  created_at: string;
  updated_at: string;
}

export interface ImportJob {
  id: number;
  import_type: string;
  file_name: string;
  status: string;
  errors_json: string[];
  result_json: Record<string, unknown>;
  created_at: string;
  finished_at: string | null;
}

export interface ApiError {
  detail?: string;
  [key: string]: unknown;
}

export interface TelegramStatus {
  enabled: boolean;
  linked: boolean;
  chat_id: number | null;
  telegram_username: string;
  bot_username: string;
  notify_manual_review: boolean;
  notify_new_submissions: boolean;
  can_manage_bot?: boolean;
  notify_all_submissions?: boolean;
}

export interface TelegramLinkCode {
  code: string;
  expires_at: string;
  start_command: string;
}

export interface TelegramBotSettings {
  enabled: boolean;
  bot_token_set: boolean;
  bot_token_masked: string;
  bot_username: string;
  http_proxy: string;
  notify_all_submissions: boolean;
  is_ready: boolean;
  updated_at: string | null;
}

export interface TelegramBotSettingsUpdate {
  enabled?: boolean;
  bot_token?: string;
  clear_bot_token?: boolean;
  bot_username?: string;
  http_proxy?: string;
  notify_all_submissions?: boolean;
}

