window.Dwainz = (function () {
  'use strict';

  var DATA_ROOT = '../../data';
  var STORAGE_KEY = 'dwainz_progress_v1';

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
    qs: qs
  };
})();
