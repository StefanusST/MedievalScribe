// Local template generation: no external AI service required.
export const topics = [
  {name: 'Love', openings: ['You are always in my thoughts.', 'I want to see you again.', 'Your smile brings me joy.', 'Perhaps you know how I feel.'], endings: ['Will you meet me in the garden?', 'You have my heart.', 'I will wait for you until morning.', 'Please stay beside me tonight.']},
  {name: 'Adventure', openings: ['You are ready for a new journey.', 'Perhaps the forest hides a secret.', 'You have a map and a sword.', 'Our adventure begins at sunrise.'], endings: ['Will you explore the castle with me?', 'I will follow you beyond the mountains.', 'Please bring your courage.', 'You will find the answer before nightfall.']},
  {name: 'Friendship', openings: ['Hello, you are my oldest friend.', 'You have always stood beside me.', 'I often think of our adventures.', 'Your friendship means everything to me.'], endings: ['I will help you through this trouble.', 'Please join me for dinner.', 'You have my trust and my word.', 'Perhaps we will meet again soon.']},
  {name: 'Royal Court', openings: ['You are welcome in the royal court.', 'The king has an important request.', 'Perhaps the queen knows the truth.', 'You have earned the respect of the kingdom.'], endings: ['Will you speak before the council?', 'Please bring your message to the throne.', 'You will receive your reward soon.', 'I want to hear your advice before the feast.']},
  {name: 'Mystery', openings: ['Perhaps someone knows where the letter is.', 'You are the only witness to this mystery.', 'The stranger has a secret.', 'You have found a clue beneath the stairs.'], endings: ['Will you tell me what you saw?', 'Please meet me before midnight.', 'I want to discover the truth.', 'You will find your answer behind the locked door.']},
];

export function generateLine(topic, previous = '', random = Math.random) {
  const choices = topic.openings.flatMap(start => topic.endings.map(end => `${start} ${end}`)).filter(line => line !== previous);
  return choices[Math.min(choices.length - 1, Math.floor(random() * choices.length))];
}
