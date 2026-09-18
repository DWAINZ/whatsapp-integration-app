window.Dwainz = (function () {
  'use strict';

  var DATA_ROOT = '../../data';
  var STORAGE_KEY = 'dwainz_progress_v1';

  // Tasteful, muted accent pairs cycled per-topic (and per-subject) so moving
  // between sections doesn't feel monotonous. Avoids pure green/red — those
  // are already used to mean "correct"/"incorrect" elsewhere in the app.
  var TOPIC_PALETTE = [
    { accent: '#2E8FE0', ink: '#1C6FB8' }, // blue
    { accent: '#14919B', ink: '#0F6E76' }, // teal
    { accent: '#C08A2E', ink: '#96690E' }, // amber
    { accent: '#7C5CBF', ink: '#5C3FA0' }, // violet
    { accent: '#B15C8C', ink: '#8C3E68' }, // mauve
    { accent: '#4A7BA6', ink: '#345A7D' }  // slate-blue
  ];
  function topicColor(index) {
    return TOPIC_PALETTE[((index % TOPIC_PALETTE.length) + TOPIC_PALETTE.length) % TOPIC_PALETTE.length];
  }

  function loadSubject(subject) {
    return fetch(DATA_ROOT + '/subjects/' + subject + '.json').then(function (r) {
      if (!r.ok) throw new Error('Could not load subject: ' + subject);
      return r.json();
    });
  }

  function loadPastQuestions(subject) {
    return fetch(DATA_ROOT + '/past-questions/' + subject + '.json').then(function (r) {
      if (!r.ok) throw new Error('Could not load past questions for: ' + subject);
      return r.json();
    });
  }

  function readAll() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : {};
    } catch (e) { return {}; }
  }
  function writeAll(data) {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(data)); } catch (e) { /* ignore (private mode etc.) */ }
  }

  function markSubtopicDone(subject, topic, subtopic, score) {
    var all = readAll();
    all[subject] = all[subject] || {};
    all[subject][topic] = all[subject][topic] || {};
    all[subject][topic][subtopic] = { done: true, correct: score.correct, total: score.total, firstTry: score.firstTry, updatedAt: Date.now() };
    writeAll(all);
  }

  function getTopicProgress(subject, topic) {
    var all = readAll();
    return (all[subject] && all[subject][topic]) || {};
  }

  function isSubtopicDone(subject, topic, subtopic) {
    var prog = getTopicProgress(subject, topic);
    return !!(prog[subtopic] && prog[subtopic].done);
  }

  function findSubtopic(subjectData, topicId, subtopicId) {
    var topic = (subjectData.topics || []).filter(function (t) { return t.id === topicId; })[0];
    if (!topic) return null;
    var subtopic = (topic.subtopics || []).filter(function (s) { return s.id === subtopicId; })[0];
    return subtopic ? { topic: topic, subtopic: subtopic } : null;
  }

  function findTopic(subjectData, topicId) {
    return (subjectData.topics || []).filter(function (t) { return t.id === topicId; })[0] || null;
  }

  function qs(name) {
    return new URLSearchParams(window.location.search).get(name);
  }

  return {
    loadSubject: loadSubject,
    loadPastQuestions: loadPastQuestions,
    markSubtopicDone: markSubtopicDone,
    getTopicProgress: getTopicProgress,
    isSubtopicDone: isSubtopicDone,
    findSubtopic: findSubtopic,
    findTopic: findTopic,
    topicColor: topicColor,
    qs: qs
  };
})();
