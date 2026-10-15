// Weekly spelling lists. Each entry shows up under "Spelling Test" in the
// sidebar as its own week.
//
// To add a new week, copy an entry and change it:
//   id        unique, used to remember which list was open
//   unit      unit number from the sheet
//   lesson    lesson number from the sheet
//   testDate  'YYYY-MM-DD' of the test. Drives the "Week of ..." label and
//             which list opens by default.
//   words     one word per string. Singular/plural pairs can be written as
//             'wolf/wolves' just like the sheet: both spellings are quizzed,
//             and the plural gets kid-style traps like "wolfs" or "feets".
//   challenge bonus words, tagged "Challenge" on the quiz.
window.HOMEWORK_HELPER_SPELLING_LISTS = [
    {
        id: 'u3-l5',
        unit: 3,
        lesson: 5,
        testDate: '2026-10-16',
        words: [
            'woman/women', 'baby/babies', 'child/children', 'mouse/mice',
            'fox/foxes', 'tooth/teeth', 'person/people', 'foot/feet',
            'glass/glasses', 'louse/lice', 'night/nights', 'man/men',
            'match/matches', 'goose/geese', 'story/stories',
        ],
        challenge: ['exercise', 'laugh'],
    },
    {
        id: 'u3-l10',
        unit: 3,
        lesson: 10,
        testDate: '2026-10-23',
        words: [
            'self/selves', 'thief/thieves', 'loaf/loaves', 'wife/wives',
            'wolf/wolves', 'elf/elves', 'knife/knives', 'life/lives',
            'shelf/shelves', 'half/halves', 'leaf/leaves',
        ],
        challenge: ['before', 'please'],
    },
    {
        id: 'u3-l14',
        unit: 3,
        lesson: 14,
        testDate: '2026-10-30',
        words: [
            'raised', 'dried', 'watched', 'submitting', 'wished',
            'knife', 'puppies', 'books', 'people', 'children',
        ],
        challenge: ['across', 'idea'],
    },
];
