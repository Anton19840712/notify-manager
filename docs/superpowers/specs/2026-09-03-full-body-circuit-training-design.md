# Full Body Circuit Training Design

## Goal

Replace the old daily strength block with a practical one-hour full-body endurance circuit that uses the user's available home equipment and avoids changing rack height inside the circuit.

## Constraints

- One EZ bar, two Olympic bars, one trap bar.
- One rack setup can be used for either squat/standing press height or bench/incline bench height during a circuit.
- Pull-up bar and dips station are available separately.
- The session is one hour, followed by a shower.
- Any remaining time in the hour goes to assault bike or regular bike.

## Training Structure

Use the existing `training` block and existing rotating-event mechanism. Replace the old seven-day "thighs + calves + one base movement" rotation with a four-day rack-setup rotation:

1. Template A: rack set for back squat and standing press.
2. Template B: rack set for bench press.
3. Template A: rack set for front squat and standing press.
4. Template B: rack set for incline press.

Every template is a 10-exercise circuit:

- 5 minutes warm-up.
- 45 minutes of circuits, up to 10 rounds of 10 reps.
- Remaining time: assault bike or regular bike.
- After the hour: shower.

## Exercise Rules

Template A uses squats from the rack and standing press, so bench pressing is excluded. Template B uses bench or incline rack height, so rack squats are excluded and legs are covered by trap bar and deadlift/RDL work.

Both templates keep pulling, pushing, calves, arms, traps/posture where relevant, and core. Rowing is barbell bent-over row, not the axis/rack attachment.

## Testing

Update the default schedule test to verify the four-day rotation, titles, message content, bike tail, shower note, and block toggling.
