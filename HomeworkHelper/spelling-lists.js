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
    {
        id: 'u4-rome',
        unit: 4,
        title: 'Ancient Rome',
        testDate: '2026-11-09',
        words: [
            'tarnish', 'marbles', 'portion', 'motor', 'circulate', 'servant',
            'turkey', 'doctor', 'worship', 'surgery', 'immortal', 'sword',
            'messenger', 'barbecue', 'giraffe', 'slurp', 'sir', 'mirth',
        ],
        challenge: ['above', 'beginning'],
        // Content words are tagged "Content Word". Keep capitals for names.
        content: ['Mediterranean'],
        // Optional hand-picked wrong answers, used before generated ones.
        distractors: {
            sir: ['sur', 'ser', 'cir', 'surr'],
            sword: ['sord', 'sowrd', 'swerd', 'soard'],
        },
    },
    {
        id: 'u4-myths',
        unit: 4,
        title: 'Roman Myths',
        testDate: '2026-11-13',
        words: [
            'Greeks', 'meter', 'Venus', 'asleep', 'secret', 'agreed', 'seed',
            'succeeded', 'cedar', 'breed', 'create', 'jamboree', 'speech',
            'degree', 'retail', 'screech', 'scenic', 'tedious',
        ],
        challenge: ['except', 'follow'],
        content: ['Psyche'],
        distractors: {
            psyche: ['syche', 'psychee', 'sykee', 'psiche'],
            except: ['exept', 'exsept', 'ecxept', 'excepte'],
            meter: ['meeter', 'meator', 'metor', 'meetur'],
            seed: ['sead', 'sede', 'seid', 'ceed'],
            breed: ['brede', 'breid', 'breede', 'bried'],
            greeks: ['greaks', 'greks', 'greecks', 'grieks'],
            follow: ['folow', 'follo', 'folloe', 'fallo'],
        },
    },
];
