const fs = require('fs');
const src = fs.readFileSync('web_client/static/modules/manual-control.js', 'utf8');
const match = src.match(/function resolveHandAction\(handType, layout\) \{[\s\S]*?\n\}/);
if (!match) {
  console.error('resolveHandAction is missing');
  process.exit(1);
}
eval(match[0]);

const cases = [
  ['gripper', { gripper: {} }, 'gripper'],
  ['hand', { hand: {} }, 'hand'],
  ['hand_as_gripper', { gripper: {} }, 'gripper'],
  ['hand', { gripper: {} }, 'gripper'],
  ['lhand_rgripper', { hand: {} }, 'hand'],
  ['gripper', { hand: {} }, 'hand'],
  ['lgripper_rhand', { hand: {} }, 'hand'],
  [undefined, {}, 'gripper'],
];
for (const [handType, layout, expected] of cases) {
  const actual = resolveHandAction(handType, layout);
  if (actual !== expected) {
    console.error(JSON.stringify({ handType, actual, expected }));
    process.exit(1);
  }
}
console.log('ok');
