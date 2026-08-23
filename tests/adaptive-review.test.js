const test = require("node:test");
const assert = require("node:assert/strict");

global.window = global;
global.FSRS = require("ts-fsrs");
require("../src/template/adaptive-review.js");

const Review = global.AdaptiveReview;
const NOW = Date.parse("2026-08-24T01:00:00Z");

function freshWord(overrides = {}) {
  return Review.normalize({
    word: "repository",
    def: "仓库，存放代码的地方",
    speech: "repository",
    audioTerm: "/vocabulary-month/audio/repository.mp3",
    examples: ["Open the repository before you edit the code."],
    lessons: ["词汇强化 Day 1"],
    course: "vocabulary-month",
    createdAt: NOW,
    updatedAt: NOW,
    ...overrides,
  }, NOW);
}

test("new cards use official FSRS four-rating scheduling", () => {
  const item = freshWord();
  const preview = Review.preview(item, NOW);
  assert.deepEqual(Object.keys(preview), ["again", "hard", "good", "easy"]);
  assert.ok(preview.again.due < preview.easy.due);
  const reviewed = Review.applyRating(item, "good", "en-zh", NOW);
  assert.equal(reviewed.lastRating, "good");
  assert.equal(reviewed.reviews, 1);
  assert.ok(reviewed.nextReview > NOW);
  assert.ok(reviewed.stability > 0);
  assert.ok(reviewed.difficulty >= 1 && reviewed.difficulty <= 10);
});

test("legacy fixed-step records migrate without losing history", () => {
  const item = freshWord({
    fsrsCard: undefined,
    reviews: 3,
    stage: 3,
    nextReview: NOW + 7 * 86400000,
    lastReviewed: NOW - 86400000,
    reviewHistory: [NOW - 86400000],
  });
  assert.equal(item.reviews, 3);
  assert.equal(item.fsrsCard.state, Review.State.Review);
  assert.equal(item.nextReview, NOW + 7 * 86400000);
  assert.equal(item.reviewHistory.length, 1);
});

test("today completion counts a word once even with multiple reviews", () => {
  const item = freshWord({ reviewLog: [
    { at: NOW, rating: "again" },
    { at: NOW + 600000, rating: "good" },
  ] });
  assert.equal(Review.reviewedToday(item, NOW + 3600000), true);
});

test("review modes rotate through active recall formats", () => {
  assert.equal(Review.prompt(freshWord({ reviews: 0 })).mode, "en-zh");
  assert.equal(Review.prompt(freshWord({ reviews: 1 })).mode, "zh-en");
  assert.equal(Review.prompt(freshWord({ reviews: 2 })).mode, "audio");
  assert.equal(Review.prompt(freshWord({ reviews: 3 })).mode, "cloze");
});

test("source labels distinguish vocabulary and speaking courses", () => {
  assert.equal(Review.sourceKey(freshWord()), "vocabulary-month");
  assert.equal(Review.sourceKey(freshWord({ course: undefined, lessons: ["Lesson 3"] })), "speaking-course");
  assert.equal(Review.sourceKey(freshWord({ course: undefined, lessons: [] })), "other");
});
