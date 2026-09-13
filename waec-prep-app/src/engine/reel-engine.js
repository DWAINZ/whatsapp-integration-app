/*
 * D'WAINZ reel engine — data-driven version of the story/lesson/quiz reel.
 * Usage: DwainzReel.init({ container, caption, stories, lessons, quizzes, ... })
 * See README in this folder for the full config shape.
 */
window.DwainzReel = (function () {
  'use strict';

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>]/g, function (c) {
      return c === '&' ? '&amp;' : c === '<' ? '&lt;' : '&gt;';
    });
  }

  function init(cfg) {
    var container = cfg.container;
    var STORIES = cfg.stories || [];
    var LESSONS = cfg.lessons || [];
    var QUIZZES = cfg.quizzes || [];
    var caption = cfg.caption || '';
    var programTitle = cfg.programTitle || '';
    var onFinish = cfg.onFinish || function () {};
    var backHref = cfg.backHref || null;
    var backLabel = cfg.backLabel || 'Back';
    var deepLinkCard = cfg.deepLinkCard || null; // 1-based lesson number to jump straight to
    var returnHref = cfg.returnHref || null;     // where the floating "back" button should go when deep-linked
    var returnLabel = cfg.returnLabel || 'Back';

    container.innerHTML =
      '<div class="dw-reel-stage">' +
        '<div class="phone" id="dwPhone">' +
          '<div class="glow"></div>' +
          (backHref ? '<a class="exitbtn" href="' + esc(backHref) + '" aria-label="' + esc(backLabel) + '">←</a>' : '') +
          '<div class="progressbar" id="dwProgressbar"></div>' +
          '<div class="balloon" id="dwBalloon">1</div>' +
          '<button class="playpause" id="dwPlaypause" aria-label="Pause">⏸</button>' +
          '<button class="voicebtn" id="dwVoicebtn" aria-pressed="false" aria-label="Turn narration on">🔇</button>' +
          '<div class="cardwrap" id="dwCardwrap"></div>' +
          '<div class="voice-warning" id="dwVoiceWarning" hidden>Voice didn’t start — try a different browser or a new tab.</div>' +
          '<button class="backbtn" id="dwBackToQ" hidden></button>' +
          '<div class="caption">' + esc(caption) + ' · <span id="dwIdxLabel">1</span>/<span id="dwTotalLabel">1</span></div>' +
          '<div class="modal-backdrop" id="dwModalBackdrop">' +
            '<div class="modal-box">' +
              '<h4 id="dwModalTitle"></h4>' +
              '<p id="dwModalBody"></p>' +
              '<div class="modal-actions">' +
                '<button class="secondary" id="dwModalSecondary" hidden></button>' +
                '<button class="primary" id="dwModalPrimary"></button>' +
              '</div>' +
            '</div>' +
          '</div>' +
        '</div>' +
      '</div>';

    var STORY_COUNT = STORIES.length;
    var LESSON_COUNT = LESSONS.length;
    var QUIZ_COUNT = QUIZZES.length;
    var LESSON_START = STORY_COUNT;
    var QUIZ_START = LESSON_START + LESSON_COUNT;
    var STATS_IDX = QUIZ_START + QUIZ_COUNT;
    var TOTAL = STATS_IDX + 1;

    function lessonCardIndex(refCard) { return LESSON_START + refCard - 1; }
    function lessonCardNumber(refCard) { return LESSON_START + refCard; }

    var progressbar = container.querySelector('#dwProgressbar');
    var cardwrap = container.querySelector('#dwCardwrap');
    for (var s = 0; s < TOTAL; s++) {
      var seg = document.createElement('div');
      seg.className = 'seg';
      seg.innerHTML = '<i></i>';
      progressbar.appendChild(seg);
    }
    container.querySelector('#dwTotalLabel').textContent = TOTAL;

    STORIES.forEach(function (st, i) {
      var html = '<div class="card" data-i="' + i + '" data-type="story">' +
        (st.tag ? '<div class="eyebrow2">' + esc(st.tag) + '</div>' : '') +
        (st.sub ? '<p class="hook">' + esc(st.sub) + '</p>' : '') +
        (st.visual || '') +
        (st.heading ? '<h2>' + esc(st.heading) + '</h2>' : '') +
        (st.list ? ('<ul>' + st.list.map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ul>') : '') +
        '</div>';
      cardwrap.insertAdjacentHTML('beforeend', html);
    });

    LESSONS.forEach(function (l, i) {
      var absIdx = LESSON_START + i;
      var html = '<div class="card" data-i="' + absIdx + '" data-type="lesson">' +
        '<div class="eyebrow2">Card ' + (absIdx + 1) + ' · ' + esc(l.eyebrow || '') + '</div>' +
        (l.big ? '<div class="bigword">' + esc(l.big) + '</div>' : '') +
        (l.heading ? '<h2>' + esc(l.heading) + '</h2>' : '') +
        (l.visual || '') +
        (l.list ? ('<ul>' + l.list.map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ul>') : '') +
        (l.sub ? '<p class="sub">' + esc(l.sub) + '</p>' : '') +
        '</div>';
      cardwrap.insertAdjacentHTML('beforeend', html);
    });

    QUIZZES.forEach(function (q, qi) {
      var absIdx = QUIZ_START + qi;
      var html = '<div class="card" data-i="' + absIdx + '" data-type="quiz">' +
        '<div class="qhead"><div class="qnum">Question ' + (qi + 1) + '</div><div class="qof">of ' + QUIZ_COUNT + ' · mastery check</div></div>' +
        '<h2>' + esc(q.question) + '</h2>' +
        '<div class="quiz-opts" data-q="' + qi + '">' +
          q.options.map(function (opt, oi) { return '<button data-q="' + qi + '" data-opt="' + oi + '">' + String.fromCharCode(65 + oi) + ' · ' + esc(opt) + '</button>'; }).join('') +
        '</div>' +
        '<div class="quiz-meta" id="dwQuizMeta' + qi + '">Attempt 1 of 3</div>' +
        '</div>';
      cardwrap.insertAdjacentHTML('beforeend', html);
    });

    cardwrap.insertAdjacentHTML('beforeend',
      '<div class="card stats" data-i="' + STATS_IDX + '" data-type="stats">' +
        '<h2>How you did</h2>' +
        '<div class="stats-scroll">' +
          '<div class="stat-rows" id="dwStatRows"></div>' +
          (QUIZ_COUNT ? (
            '<div class="viz-title">Correct vs incorrect</div><div id="dwVizDonut"></div>' +
            '<div class="viz-title">Attempts per question</div><div id="dwVizBars"></div>' +
            '<div class="viz-title">How questions were solved</div><div id="dwVizStack"></div>'
          ) : '') +
        '</div>' +
        (backHref ? '<a class="pill-btn" href="' + esc(backHref) + '" style="text-decoration:none;text-align:center;">' + esc(backLabel) + ' →</a>' : '') +
      '</div>'
    );

    var cards = Array.prototype.slice.call(cardwrap.querySelectorAll('.card'));
    var segs = Array.prototype.slice.call(progressbar.querySelectorAll('.seg'));

    var phone = container.querySelector('#dwPhone');
    var playpause = container.querySelector('#dwPlaypause');
    var voicebtn = container.querySelector('#dwVoicebtn');
    var idxLabel = container.querySelector('#dwIdxLabel');
    var backToQ = container.querySelector('#dwBackToQ');
    var voiceWarning = container.querySelector('#dwVoiceWarning');
    var balloon = container.querySelector('#dwBalloon');

    var idx = 0;
    var explicitPaused = false;
    var holdPaused = false;
    var voiceOn = false;
    var selectedVoice = null;
    var keepAliveTimer = null;
    var voiceWatchdog = null;
    var pendingReview = null; // {returnTo, target} internal, or {returnHref, target} external
    var startTime = Date.now();

    var quizState = QUIZZES.map(function () { return { cycleAttempts: 0, totalAttempts: 0, everAnswered: false, lastCorrect: null, firstTryCorrect: false }; });
    function computeScore() {
      var correct = 0, firstTry = 0, totalAtt = 0;
      quizState.forEach(function (st) {
        if (st.lastCorrect === true) correct++;
        if (st.firstTryCorrect === true) firstTry++;
        totalAtt += st.totalAttempts;
      });
      return { correct: correct, firstTry: firstTry, totalAtt: totalAtt, total: QUIZ_COUNT };
    }

    function pickMaleVoice() {
      if (!('speechSynthesis' in window)) return null;
      var voices = window.speechSynthesis.getVoices();
      if (!voices.length) return null;
      var isFemale = /female|zira|samantha|victoria|karen|moira|tessa|susan|linda|amy|emma|joanna|salli|kimberly/i;
      var isMale = /male|david|daniel|alex|fred|george|james|mark|paul|guy|arthur|ryan|thomas|oliver|matthew|brian/i;
      var named = voices.filter(function (v) { return isMale.test(v.name) && !isFemale.test(v.name); });
      var namedEn = named.filter(function (v) { return /^en/i.test(v.lang); });
      if (namedEn.length) return namedEn[0];
      if (named.length) return named[0];
      var plainEn = voices.filter(function (v) { return /^en/i.test(v.lang) && !isFemale.test(v.name); });
      if (plainEn.length) return plainEn[0];
      return voices[0];
    }
    if ('speechSynthesis' in window) {
      selectedVoice = pickMaleVoice();
      window.speechSynthesis.onvoiceschanged = function () { selectedVoice = pickMaleVoice(); };
      window.speechSynthesis.cancel();
    } else {
      voicebtn.disabled = true;
      voicebtn.title = "Voice narration isn't supported in this browser";
    }

    function clearKeepAlive() { if (keepAliveTimer) { clearInterval(keepAliveTimer); keepAliveTimer = null; } }
    function startKeepAlive() {
      clearKeepAlive();
      keepAliveTimer = setInterval(function () {
        if (!('speechSynthesis' in window)) return clearKeepAlive();
        if (window.speechSynthesis.speaking) { window.speechSynthesis.pause(); window.speechSynthesis.resume(); }
        else clearKeepAlive();
      }, 4000);
    }
    function speak(text) {
      if (!('speechSynthesis' in window) || !text) return;
      var synth = window.speechSynthesis;
      synth.cancel();
      clearKeepAlive();
      voiceWarning.hidden = true;
      clearTimeout(voiceWatchdog);
      setTimeout(function () {
        var u = new SpeechSynthesisUtterance(text);
        if (selectedVoice) u.voice = selectedVoice;
        u.rate = 0.98; u.pitch = 0.85; u.volume = 1;
        u.onstart = startKeepAlive;
        u.onend = clearKeepAlive;
        u.onerror = function () { clearKeepAlive(); voiceWarning.hidden = false; };
        synth.speak(u);
        voiceWatchdog = setTimeout(function () { if (!synth.speaking) voiceWarning.hidden = false; }, 1200);
      }, 40);
    }
    function stopSpeaking() { if ('speechSynthesis' in window) window.speechSynthesis.cancel(); clearKeepAlive(); }

    function getNarration(i) {
      if (i < STORY_COUNT) return STORIES[i].narration || '';
      if (i < QUIZ_START) return LESSONS[i - LESSON_START].narration || '';
      if (i < STATS_IDX) return QUIZZES[i - QUIZ_START].narration || '';
      if (i === STATS_IDX) {
        var sc = computeScore();
        return QUIZ_COUNT ? ('You scored ' + sc.correct + ' out of ' + QUIZ_COUNT + ', with ' + sc.firstTry + ' correct on the first try.') : 'You have finished this lesson.';
      }
      return '';
    }
    function maybeSpeakCurrent() { if (voiceOn) speak(getNarration(idx)); }

    voicebtn.addEventListener('click', function () {
      voiceOn = !voiceOn;
      voicebtn.textContent = voiceOn ? '🔊' : '🔇';
      voicebtn.setAttribute('aria-pressed', voiceOn ? 'true' : 'false');
      voicebtn.setAttribute('aria-label', voiceOn ? 'Turn narration off' : 'Turn narration on');
      if (voiceOn) {
        if (!selectedVoice) selectedVoice = pickMaleVoice();
        speak(getNarration(idx));
      } else {
        stopSpeaking();
        voiceWarning.hidden = true;
      }
    });

    function applyPausedState() {
      var p = explicitPaused || holdPaused;
      phone.classList.toggle('paused', p);
      if ('speechSynthesis' in window) {
        if (p && window.speechSynthesis.speaking) window.speechSynthesis.pause();
        else if (!p && window.speechSynthesis.paused) window.speechSynthesis.resume();
      }
    }
    playpause.addEventListener('click', function () {
      explicitPaused = !explicitPaused;
      playpause.textContent = explicitPaused ? '▶' : '⏸';
      playpause.setAttribute('aria-label', explicitPaused ? 'Play' : 'Pause');
      applyPausedState();
    });
    cardwrap.addEventListener('pointerdown', function (e) {
      if (e.target.closest('button, input')) return;
      holdPaused = true; applyPausedState();
    });
    ['pointerup', 'pointercancel', 'pointerleave'].forEach(function (evt) {
      document.addEventListener(evt, function () { if (holdPaused) { holdPaused = false; applyPausedState(); } });
    });

    function updateBalloon() {
      var segEl = segs[idx];
      var pbRect = progressbar.getBoundingClientRect();
      var segRect = segEl.getBoundingClientRect();
      var centerX = segRect.left - pbRect.left + segRect.width / 2;
      balloon.style.left = centerX + 'px';
      balloon.textContent = idx + 1;
    }
    window.addEventListener('resize', updateBalloon);

    function updateBackButton() {
      if (pendingReview && idx === pendingReview.target) {
        backToQ.hidden = false;
        backToQ.textContent = pendingReview.label || ('↩ Back to Question ' + ((pendingReview.returnTo - QUIZ_START) + 1));
      } else {
        backToQ.hidden = true;
      }
    }
    backToQ.addEventListener('click', function () {
      var pr = pendingReview; pendingReview = null;
      if (pr.returnHref) { window.location.href = pr.returnHref; return; }
      goTo(pr.returnTo, { auto: false });
    });

    function renderQuizVisual(qi) {
      var group = cardwrap.querySelector('.quiz-opts[data-q="' + qi + '"]');
      var meta = container.querySelector('#dwQuizMeta' + qi);
      if (!group) return;
      var st = quizState[qi]; var q = QUIZZES[qi];
      var buttons = Array.prototype.slice.call(group.querySelectorAll('button'));
      buttons.forEach(function (b) { b.classList.remove('correct', 'wrong'); b.disabled = false; });
      if (st.lastCorrect) {
        buttons[q.correctIdx].classList.add('correct');
        meta.textContent = 'Last attempt: correct ✓ · tap to try again';
      } else {
        if (st.chosenIdx !== undefined) buttons[st.chosenIdx].classList.add('wrong');
        buttons[q.correctIdx].classList.add('correct');
        meta.textContent = 'Last attempt: incorrect ✗ · tap to try again';
      }
    }
    function renderQuizArrival(qi) {
      var group = cardwrap.querySelector('.quiz-opts[data-q="' + qi + '"]');
      var meta = container.querySelector('#dwQuizMeta' + qi);
      if (!group) return;
      var st = quizState[qi];
      var buttons = Array.prototype.slice.call(group.querySelectorAll('button'));
      buttons.forEach(function (b) { b.classList.remove('correct', 'wrong'); b.disabled = false; });
      meta.textContent = st.everAnswered
        ? (st.lastCorrect ? 'Last attempt: correct ✓ · tap to try again' : 'Last attempt: incorrect ✗ · tap to try again')
        : 'Attempt 1 of 3';
    }

    function render() {
      cards.forEach(function (c, i) { c.classList.toggle('active', i === idx); });
      segs.forEach(function (s, i) {
        s.classList.remove('active', 'done', 'no-anim');
        if (i < idx) s.classList.add('done');
        if (i === idx) {
          s.classList.add('active');
          if (idx >= QUIZ_START) s.classList.add('no-anim');
        }
      });
      idxLabel.textContent = idx + 1;
      updateBalloon();
      if (idx >= QUIZ_START && idx < STATS_IDX) {
        var qi = idx - QUIZ_START;
        quizState[qi].cycleAttempts = 0;
        renderQuizArrival(qi);
      }
      if (idx === STATS_IDX) { renderStats(); onFinish(computeScore()); }
      updateBackButton();
    }

    function goTo(newIdx, opts) {
      opts = opts || {};
      if (newIdx < 0 || newIdx >= TOTAL) return;
      stopSpeaking();
      voiceWarning.hidden = true;
      if (!opts.auto) { explicitPaused = true; playpause.textContent = '▶'; playpause.setAttribute('aria-label', 'Play'); applyPausedState(); }
      idx = newIdx;
      if (pendingReview) {
        if (idx !== pendingReview.target && idx !== pendingReview.returnTo) pendingReview = null;
        else if (idx === pendingReview.returnTo) pendingReview = null;
      }
      render();
      maybeSpeakCurrent();
    }

    function currentIsLockedQuiz() {
      if (idx < QUIZ_START || idx >= STATS_IDX) return false;
      return !quizState[idx - QUIZ_START].everAnswered;
    }
    function shakeCurrent() {
      var el = cards[idx];
      el.classList.remove('shake'); void el.offsetWidth; el.classList.add('shake');
    }
    function userNext() {
      if (currentIsLockedQuiz()) { shakeCurrent(); return; }
      goTo(idx + 1, { auto: false });
    }
    function userPrev() { goTo(idx - 1, { auto: false }); }

    phone.addEventListener('click', function (e) {
      if (e.target.closest('button, input, a, .modal-backdrop, .progressbar')) return;
      var rect = phone.getBoundingClientRect();
      var frac = (e.clientX - rect.left) / rect.width;
      if (frac < 0.2) userPrev();
      else if (frac > 0.8) userNext();
    });

    progressbar.addEventListener('click', function (e) {
      var segEl = e.target.closest('.seg');
      if (!segEl) return;
      var i = segs.indexOf(segEl);
      if (i >= 0) goTo(i, { auto: false });
    });

    progressbar.addEventListener('animationend', function (e) {
      if (explicitPaused) return;
      if (e.target.tagName === 'I' && e.target.closest('.seg.active')) goTo(idx + 1, { auto: true });
    });

    var modalBackdrop = container.querySelector('#dwModalBackdrop');
    var modalTitle = container.querySelector('#dwModalTitle');
    var modalBody = container.querySelector('#dwModalBody');
    var modalPrimary = container.querySelector('#dwModalPrimary');
    var modalSecondary = container.querySelector('#dwModalSecondary');

    function openModal(mcfg) {
      modalTitle.textContent = mcfg.title;
      modalBody.textContent = mcfg.body;
      modalPrimary.textContent = mcfg.primaryLabel;
      modalPrimary.onclick = mcfg.onPrimary;
      if (mcfg.secondaryLabel) {
        modalSecondary.hidden = false;
        modalSecondary.textContent = mcfg.secondaryLabel;
        modalSecondary.onclick = mcfg.onSecondary;
      } else {
        modalSecondary.hidden = true;
      }
      modalBackdrop.classList.add('show');
    }
    function closeModal() { modalBackdrop.classList.remove('show'); }

    cardwrap.addEventListener('click', function (e) {
      var btn = e.target.closest('button[data-opt]');
      if (!btn) return;
      var qi = parseInt(btn.dataset.q, 10);
      var optIdx = parseInt(btn.dataset.opt, 10);
      var st = quizState[qi];
      var q = QUIZZES[qi];
      st.cycleAttempts++; st.totalAttempts++;
      st.chosenIdx = optIdx;
      var isCorrect = optIdx === q.correctIdx;
      var cardIdx = QUIZ_START + qi;
      if (!st.everAnswered) { st.everAnswered = true; st.firstTryCorrect = isCorrect; }
      st.lastCorrect = isCorrect;

      if (isCorrect) {
        renderQuizVisual(qi);
        openModal({
          title: 'Correct! 🎉',
          body: q.explainCorrect,
          primaryLabel: 'Proceed →',
          onPrimary: function () { closeModal(); goTo(cardIdx + 1, { auto: false }); }
        });
        if (voiceOn) speak('Correct! ' + q.explainCorrect);
      } else {
        var canRetry = st.cycleAttempts < 3;
        renderQuizVisual(qi);
        openModal({
          title: canRetry ? 'Not quite' : 'Last try used',
          body: q.explainWrong,
          secondaryLabel: 'Review Card ' + lessonCardNumber(q.refCard),
          onSecondary: function () {
            closeModal();
            pendingReview = { returnTo: cardIdx, target: lessonCardIndex(q.refCard) };
            goTo(lessonCardIndex(q.refCard), { auto: false });
          },
          primaryLabel: canRetry ? 'Try Again' : 'Continue →',
          onPrimary: function () {
            closeModal();
            if (canRetry) { st.chosenIdx = undefined; renderQuizArrival(qi); }
            else { goTo(cardIdx + 1, { auto: false }); }
          }
        });
        if (voiceOn) speak(q.explainWrong);
      }
    });

    function renderStats() {
      var elapsedMs = Date.now() - startTime;
      var mins = Math.floor(elapsedMs / 60000), secs = Math.floor((elapsedMs % 60000) / 1000);
      var timeStr = mins + 'm ' + (secs < 10 ? '0' : '') + secs + 's';
      var sc = computeScore();
      var correctCount = sc.correct, firstTryCount = sc.firstTry, totalAttempts = sc.totalAtt;
      var rows = '<div class="stat-row"><span>Time spent</span><span>' + timeStr + '</span></div>';
      if (QUIZ_COUNT) {
        var accuracy = Math.round((correctCount / QUIZ_COUNT) * 100);
        var incorrect = QUIZ_COUNT - correctCount;
        rows =
          '<div class="stat-row"><span>Questions</span><span>' + QUIZ_COUNT + '</span></div>' +
          '<div class="stat-row"><span>Correct (latest attempt)</span><span>' + correctCount + '/' + QUIZ_COUNT + '</span></div>' +
          '<div class="stat-row"><span>First-try correct</span><span>' + firstTryCount + '/' + QUIZ_COUNT + '</span></div>' +
          '<div class="stat-row"><span>Total attempts used</span><span>' + totalAttempts + '</span></div>' +
          '<div class="stat-row"><span>Accuracy</span><span>' + accuracy + '%</span></div>' +
          rows;
        container.querySelector('#dwStatRows').innerHTML = rows;

        var R = 32, C = 2 * Math.PI * R;
        var correctLen = C * (correctCount / QUIZ_COUNT);
        container.querySelector('#dwVizDonut').innerHTML =
          '<div class="donut-wrap">' +
            '<svg viewBox="0 0 80 80">' +
              '<circle cx="40" cy="40" r="' + R + '" fill="none" stroke="rgba(30,80,140,.12)" stroke-width="10"/>' +
              '<circle cx="40" cy="40" r="' + R + '" fill="none" stroke="#12946B" stroke-width="10" ' +
                'stroke-dasharray="' + correctLen + ' ' + (C - correctLen) + '" stroke-linecap="round" transform="rotate(-90 40 40)"/>' +
              '<text x="40" y="45" text-anchor="middle" font-family="IBM Plex Mono, monospace" font-size="14" font-weight="700" fill="#16202B">' + accuracy + '%</text>' +
            '</svg>' +
            '<div class="legend">' +
              '<div><span class="dot" style="background:#12946B"></span>Correct — ' + correctCount + '</div>' +
              '<div><span class="dot" style="background:rgba(30,80,140,.2)"></span>Incorrect — ' + incorrect + '</div>' +
            '</div>' +
          '</div>';

        var maxA = Math.max(3, Math.max.apply(null, quizState.map(function (st) { return st.totalAttempts; })));
        container.querySelector('#dwVizBars').innerHTML =
          '<div class="barchart">' +
            quizState.map(function (st, i) {
              var h = Math.max(8, Math.round((st.totalAttempts / maxA) * 40));
              return '<div class="bar"><i style="height:' + h + 'px"></i><span>Q' + (i + 1) + '</span></div>';
            }).join('') +
          '</div>';

        var oneTry = 0, twoTry = 0, threeTry = 0;
        quizState.forEach(function (st) {
          if (st.totalAttempts <= 1) oneTry++; else if (st.totalAttempts === 2) twoTry++; else threeTry++;
        });
        function segb(n, color) { return n > 0 ? '<div style="width:' + (n / QUIZ_COUNT * 100) + '%;background:' + color + '"></div>' : ''; }
        container.querySelector('#dwVizStack').innerHTML =
          '<div class="stackbar">' + segb(oneTry, '#12946B') + segb(twoTry, '#2E8FE0') + segb(threeTry, '#D14343') + '</div>' +
          '<div class="legend" style="margin-top:6px;">' +
            '<div><span class="dot" style="background:#12946B"></span>1 attempt — ' + oneTry + '</div>' +
            '<div><span class="dot" style="background:#2E8FE0"></span>2 attempts — ' + twoTry + '</div>' +
            '<div><span class="dot" style="background:#D14343"></span>3+ attempts — ' + threeTry + '</div>' +
          '</div>';
      } else {
        container.querySelector('#dwStatRows').innerHTML = rows;
      }
    }

    render();

    if (deepLinkCard) {
      pendingReview = { returnTo: idx, target: lessonCardIndex(deepLinkCard), returnHref: returnHref, label: returnLabel };
      goTo(lessonCardIndex(deepLinkCard), { auto: false });
    }

    return {
      goTo: goTo,
      computeScore: computeScore,
      TOTAL: TOTAL
    };
  }

  return { init: init };
})();
