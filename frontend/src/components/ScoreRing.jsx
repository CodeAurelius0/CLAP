/**
 * ScoreRing — Circular progress indicator for the readiness score.
 */
export default function ScoreRing({ score, maxScore = 100 }) {
  const radius = 50;
  const circumference = 2 * Math.PI * radius;
  const pct = Math.min(score / maxScore, 1);
  const offset = circumference * (1 - pct);

  // Color based on score
  let color = 'var(--success-fg)';
  if (score < 50) color = 'var(--danger-fg)';
  else if (score < 75) color = 'var(--warning-fg)';

  return (
    <div className="score-container">
      <div className="score-ring">
        <svg viewBox="0 0 120 120" width="120" height="120">
          <circle className="score-ring-bg" cx="60" cy="60" r={radius} />
          <circle
            className="score-ring-progress"
            cx="60"
            cy="60"
            r={radius}
            stroke={color}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
          />
        </svg>
        <div className="score-ring-label">
          <span className="score-value">{score}</span>
          <span className="score-max">/ {maxScore}</span>
        </div>
      </div>
      <span className="score-label">GitHub Readiness</span>
    </div>
  );
}
