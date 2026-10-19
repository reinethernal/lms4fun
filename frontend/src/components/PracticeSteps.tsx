import { isRunOnlyTask } from '@/utils/taskKind';

export { isRunOnlyTask };

const PRACTICE_STEPS = [
  { id: 1, label: 'Прочитай задание' },
  { id: 2, label: 'Измени код' },
  { id: 3, label: 'Проверь программу' },
  { id: 4, label: 'Сдай задание' },
] as const;

const RUN_ONLY_STEPS = [
  { id: 1, label: 'Прочитай задание' },
  { id: 2, label: 'Запусти пример' },
] as const;

interface PracticeStepsProps {
  codeChanged: boolean;
  taskViewed: boolean;
  hasTrialRun: boolean;
  trialRunSuccess: boolean;
  submitAccepted: boolean;
  submitSubmitted: boolean;
  runOnlyTask: boolean;
}

function stepFlags(props: PracticeStepsProps) {
  const step1Done = props.taskViewed;
  if (props.runOnlyTask) {
    const step2Done = props.hasTrialRun;
    return { step1Done, step2Done, step3Done: false, step4Done: false, step4Submitted: false };
  }
  const step2Done = props.codeChanged;
  const step3Done = props.hasTrialRun && props.trialRunSuccess;
  const step4Done = props.submitAccepted;
  const step4Submitted = props.submitSubmitted;
  return { step1Done, step2Done, step3Done, step4Done, step4Submitted };
}

function stepState(
  stepId: number,
  props: PracticeStepsProps,
): 'done' | 'active' | 'upcoming' {
  const { step1Done, step2Done, step3Done, step4Done, step4Submitted } = stepFlags(props);

  if (props.runOnlyTask) {
    if (stepId === 1) {
      return step1Done ? 'done' : 'active';
    }
    if (stepId === 2) {
      if (step2Done) return 'done';
      if (step1Done) return 'active';
      return 'upcoming';
    }
    return 'upcoming';
  }

  if (step4Done) {
    return 'done';
  }
  if (stepId === 1) {
    return step1Done ? 'done' : 'active';
  }
  if (stepId === 2) {
    if (step2Done) return 'done';
    if (step1Done) return 'active';
    return 'upcoming';
  }
  if (stepId === 3) {
    if (step3Done) return 'done';
    if (step2Done) return 'active';
    return 'upcoming';
  }
  if (stepId === 4) {
    if (step4Done) return 'done';
    if (step4Submitted) return 'done';
    if (step3Done) return 'active';
    return 'upcoming';
  }
  return 'upcoming';
}

export function canRunPractice(props: PracticeStepsProps): boolean {
  return stepFlags(props).step1Done;
}

export function canSubmitPractice(props: PracticeStepsProps): boolean {
  if (props.runOnlyTask) return false;
  const flags = stepFlags(props);
  return flags.step2Done && flags.step3Done;
}

export function PracticeSteps(props: PracticeStepsProps) {
  const steps = props.runOnlyTask ? RUN_ONLY_STEPS : PRACTICE_STEPS;

  return (
    <ol className="practice-steps">
      {steps.map((step) => {
        const state = stepState(step.id, props);
        return (
          <li key={step.id} className={`practice-step practice-step-${state}`}>
            <span className="practice-step-marker" aria-hidden>
              {state === 'done' ? '✓' : step.id}
            </span>
            <span className="practice-step-label">{step.label}</span>
          </li>
        );
      })}
    </ol>
  );
}
