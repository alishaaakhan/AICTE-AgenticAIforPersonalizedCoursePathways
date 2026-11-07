/**
 * LearnMate – app.js
 * Single-page application logic for all 4 tabs:
 *   Chat | Roadmap | Progress | Skill Quiz
 * Communicates with Flask API endpoints in app.py
 */

const App = (() => {

  /* ── State ─────────────────────────────────────────── */
  let state = {
    studentId:    null,
    studentName:  null,
    domain:       null,
    skillLevel:   'beginner',
    llmAvailable: false,
    ob: { name: '', domain: '', level: 'beginner', goal: '', hours: 5, style: 'mixed' },
    currentQuestion: '',
    questionCount: 0,
    totalScore: 0,
    roadmapData: [],         // cached for PDF
    _chartDonut: null,       // Chart.js instances
    _chartBar:   null,
  };

  /* ── Theme ──────────────────────────────────────────── */
  function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('lm-theme', theme);
    // update active button
    document.querySelectorAll('.theme-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.theme === theme);
    });
  }
  // Restore saved theme on load
  (function() {
    const saved = localStorage.getItem('lm-theme');
    if (saved) setTheme(saved);
  })();

  /* ── Init ──────────────────────────────────────────── */
  function init() {
    fetchDomains();
    // Level card clicks
    document.querySelectorAll('.level-card').forEach(card => {
      card.addEventListener('click', () => {
        document.querySelectorAll('.level-card').forEach(c => c.classList.remove('active'));
        card.classList.add('active');
        state.ob.level = card.dataset.level;
      });
    });
  }

  /* ── Domains ───────────────────────────────────────── */
  async function fetchDomains() {
    try {
      const res = await fetch('/api/domains');
      const data = await res.json();
      const grid = document.getElementById('domain-grid');
      grid.innerHTML = '';
      const icons = {
        'Frontend Development': '🖥',
        'Backend Development': '⚙️',
        'Full Stack Development': '🔗',
        'Data Science & Machine Learning': '🤖',
        'Cybersecurity': '🔒',
        'UI/UX Design': '🎨',
        'Mobile Development': '📱',
        'Cloud Computing': '☁️',
        'DevOps & MLOps': '🚀',
        'Blockchain': '⛓',
        'Game Development': '🎮',
        'Embedded Systems & IoT': '🔧',
      };
      data.domains.forEach((d, i) => {
        const el = document.createElement('div');
        el.className = 'domain-chip' + (i === 0 ? ' selected' : '');
        el.textContent = (icons[d] || '📚') + ' ' + d;
        el.dataset.domain = d;
        if (i === 0) state.ob.domain = d;
        el.addEventListener('click', () => {
          document.querySelectorAll('.domain-chip').forEach(c => c.classList.remove('selected'));
          el.classList.add('selected');
          state.ob.domain = d;
        });
        grid.appendChild(el);
      });
    } catch (e) { console.error('fetchDomains', e); }
  }

  /* ── Onboarding flow ────────────────────────────────── */
  function onboardNext(step) {
    if (step === 1) {
      const name = document.getElementById('ob-name').value.trim();
      if (!name) { alert('Please enter your name.'); return; }
      state.ob.name = name;
    }
    if (step === 2 && !state.ob.domain) {
      alert('Please choose a domain.'); return;
    }
    showStep(step + 1);
  }

  function onboardBack(step) {
    showStep(step - 1);
  }

  async function onboardSubmit() {
    state.ob.goal  = document.getElementById('ob-goal').value.trim() || 'Become a professional';
    state.ob.hours = parseInt(document.getElementById('ob-hours').value) || 5;
    state.ob.style = document.getElementById('ob-style').value;

    showStep('loading');
    document.getElementById('loading-msg').textContent =
      'Building your personalized roadmap with IBM Granite…';

    try {
      const res = await fetch('/api/session/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name:            state.ob.name,
          domain:          state.ob.domain,
          skill_level:     state.ob.level,
          goal:            state.ob.goal,
          weekly_hours:    state.ob.hours,
          preferred_style: state.ob.style,
        }),
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      onSessionLoaded(data);
    } catch (e) {
      alert('Error starting session: ' + e.message);
      showStep(4);
    }
  }

  function onSessionLoaded(data) {
    const p = data.profile;
    state.studentId    = p.student_id;
    state.studentName  = p.name;
    state.domain       = p.primary_domain;
    state.llmAvailable = data.llm_available;

    // Populate sidebar
    document.getElementById('sidebar-name').textContent   = p.name;
    document.getElementById('sidebar-domain').textContent = p.primary_domain;
    document.getElementById('sidebar-avatar').textContent = p.name[0].toUpperCase();

    // Populate topbar
    const initials = p.name[0].toUpperCase();
    const tbAvatar = document.getElementById('topbar-avatar');
    const tbName   = document.getElementById('topbar-username');
    if (tbAvatar) tbAvatar.textContent = initials;
    if (tbName)   tbName.textContent   = p.name;

    // IBM badge
    if (state.llmAvailable) {
      document.getElementById('llm-badge').classList.remove('hidden');
    } else {
      document.getElementById('llm-badge-off').classList.remove('hidden');
    }

    // Show app
    document.getElementById('onboarding-overlay').classList.remove('active');
    const app = document.getElementById('app');
    app.classList.remove('hidden');
    app.style.display = 'grid';

    // Welcome message
    const isNew = data.is_new;
    const greet = isNew
      ? `Hi **${p.name}**! 🎉 I've built your personalized roadmap for **${p.primary_domain}**. Use the **Roadmap** tab to see it, or ask me anything here!`
      : `Welcome back, **${p.name}**! 🚀 You've completed **${p.completed_count}** course(s). Keep going!`;
    appendBotMessage(greet);

    // Pre-load roadmap
    loadRoadmap();
  }

  function showStep(n) {
    document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
    const el = document.getElementById(n === 'loading' ? 'step-loading' : `step-${n}`);
    if (el) el.classList.add('active');
  }

  function newSession() {
    state.studentId = null;
    document.getElementById('app').style.display = 'none';
    document.getElementById('app').classList.add('hidden');
    document.getElementById('onboarding-overlay').classList.add('active');
    document.getElementById('chat-window').innerHTML = '';
    showStep(1);
  }

  /* ── Tab switching ──────────────────────────────────── */
  function switchTab(name) {
    document.querySelectorAll('.tab').forEach(t => {
      t.classList.remove('active');
      t.classList.add('hidden');
    });
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

    const tab = document.getElementById(`tab-${name}`);
    tab.classList.remove('hidden');
    tab.classList.add('active');
    document.querySelector(`[data-tab="${name}"]`).classList.add('active');

    if (name === 'roadmap')  loadRoadmap();
    if (name === 'progress') loadProgress();
  }

  /* ── Chat ───────────────────────────────────────────── */
  async function sendChat() {
    const input = document.getElementById('chat-input');
    const msg   = input.value.trim();
    if (!msg || !state.studentId) return;
    input.value = '';
    appendUserMessage(msg);
    const typingEl = appendTyping();
    try {
      const res  = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_id: state.studentId, message: msg }),
      });
      const data = await res.json();
      typingEl.remove();
      appendBotMessage(data.reply || data.error || '…');

      // If user asked about roadmap, auto-switch tab
      const lower = msg.toLowerCase();
      if (lower.includes('roadmap') || lower.includes('show my plan')) {
        setTimeout(() => switchTab('roadmap'), 600);
      }
      if (lower.includes('progress') || lower.includes('how am i doing')) {
        setTimeout(() => switchTab('progress'), 600);
      }
    } catch (e) {
      typingEl.remove();
      appendBotMessage('Sorry, there was a network error. Please try again.');
    }
  }

  function quickChat(msg) {
    document.getElementById('chat-input').value = msg;
    sendChat();
  }

  function appendUserMessage(text) {
    const win = document.getElementById('chat-window');
    win.insertAdjacentHTML('beforeend', `
      <div class="msg user">
        <div class="msg-avatar">👤</div>
        <div class="msg-bubble">${escHtml(text)}</div>
      </div>`);
    win.scrollTop = win.scrollHeight;
  }

  function appendBotMessage(text) {
    const win = document.getElementById('chat-window');
    win.insertAdjacentHTML('beforeend', `
      <div class="msg bot">
        <div class="msg-avatar">🤖</div>
        <div class="msg-bubble">${mdToHtml(text)}</div>
      </div>`);
    win.scrollTop = win.scrollHeight;
  }

  function appendTyping() {
    const win = document.getElementById('chat-window');
    win.insertAdjacentHTML('beforeend', `
      <div class="msg bot msg-typing" id="typing-indicator">
        <div class="msg-avatar">🤖</div>
        <div class="msg-bubble">
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
        </div>
      </div>`);
    win.scrollTop = win.scrollHeight;
    return document.getElementById('typing-indicator');
  }

  /* ── Roadmap ────────────────────────────────────────── */
  async function loadRoadmap() {
    if (!state.studentId) return;
    const container = document.getElementById('roadmap-container');
    container.innerHTML = '<div class="empty-state"><div class="spinner" style="margin:0 auto"></div></div>';
    try {
      const res  = await fetch(`/api/roadmap?student_id=${state.studentId}`);
      const data = await res.json();
      renderRoadmap(data.roadmap || []);
    } catch (e) {
      container.innerHTML = '<div class="empty-state">Failed to load roadmap.</div>';
    }
  }

  /* ── PDF Export ─────────────────────────────────────── */
  function exportRoadmapPDF() {
    // Switch to roadmap tab so print captures it
    switchTab('roadmap');
    setTimeout(() => window.print(), 400);
  }

  function renderRoadmap(roadmap) {
    state.roadmapData = roadmap;   // cache for PDF
    const container = document.getElementById('roadmap-container');
    if (!roadmap.length) {
      container.innerHTML = '<div class="empty-state">No roadmap yet. Try regenerating!</div>';
      return;
    }
    container.innerHTML = '';
    roadmap.forEach(phase => {
      const phaseEl = document.createElement('div');
      phaseEl.className = 'phase-block';
      const courses = phase.courses || [];
      phaseEl.innerHTML = `
        <div class="phase-header">
          <div class="phase-num">${phase.phase}</div>
          <div class="phase-title">${escHtml(phase.phase_title || '')}</div>
          <div class="phase-weeks">~${phase.duration_weeks || '?'} weeks</div>
        </div>
        <div class="course-list">
          ${courses.map(c => renderCourseRow(c)).join('')}
        </div>`;
      container.appendChild(phaseEl);
    });
    // Bind action buttons
    container.querySelectorAll('[data-action]').forEach(btn => {
      btn.addEventListener('click', handleCourseAction);
    });
  }

  function renderCourseRow(c) {
    const levelClass = `level-${c.level || 'beginner'}`;
    const skills = (c.skills_taught || []).slice(0, 3).join(', ');
    return `
      <div class="course-row" data-id="${escHtml(c.id || '')}">
        <div class="course-info">
          <div class="course-title">${escHtml(c.title || '')}</div>
          <div class="course-meta">
            ${escHtml(c.provider || '')} · ${c.duration_weeks || '?'} weeks
            ${skills ? ' · ' + escHtml(skills) : ''}
          </div>
          ${c.why ? `<div class="course-why">${escHtml(c.why)}</div>` : ''}
        </div>
        <span class="level-pill ${levelClass}">${c.level || ''}</span>
        <div class="course-actions">
          <button class="btn-xs btn-open" data-action="open" data-url="${escHtml(c.url || '#')}">
            Open ↗
          </button>
          <button class="btn-xs btn-start" data-action="start" data-course='${JSON.stringify(c).replace(/'/g, "&#39;")}'>
            Start
          </button>
          <button class="btn-xs btn-done" data-action="done" data-id="${escHtml(c.id || '')}" data-title="${escHtml(c.title || '')}">
            Done ✓
          </button>
        </div>
      </div>`;
  }

  async function handleCourseAction(e) {
    const btn    = e.currentTarget;
    const action = btn.dataset.action;

    if (action === 'open') {
      window.open(btn.dataset.url, '_blank');
      return;
    }
    if (action === 'start') {
      let course;
      try { course = JSON.parse(btn.dataset.course.replace(/&#39;/g, "'")); }
      catch { return; }
      await fetch('/api/course/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_id: state.studentId, course }),
      });
      btn.textContent = '📖 In Progress';
      btn.disabled = true;
    }
    if (action === 'done') {
      const courseId    = btn.dataset.id;
      const courseTitle = btn.dataset.title;
      openRatingModal(courseId, courseTitle);
    }
  }

  async function regenerateRoadmap() {
    const container = document.getElementById('roadmap-container');
    container.innerHTML = '<div class="empty-state"><div class="spinner" style="margin:0 auto"></div></div>';
    try {
      const res  = await fetch('/api/roadmap/regenerate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_id: state.studentId }),
      });
      const data = await res.json();
      renderRoadmap(data.roadmap || []);
    } catch (e) {
      container.innerHTML = '<div class="empty-state">Regeneration failed.</div>';
    }
  }

  /* ── Rating modal ───────────────────────────────────── */
  let _pendingComplete = { courseId: null, title: null };

  function openRatingModal(courseId, title) {
    _pendingComplete = { courseId, title };
    document.getElementById('rating-title').textContent = title;
    setStars(0);
    document.getElementById('rating-overlay').classList.add('show');
  }

  function closeRatingModal() {
    document.getElementById('rating-overlay').classList.remove('show');
  }

  function setStars(n) {
    document.querySelectorAll('.star-btn').forEach((s, i) => {
      s.classList.toggle('lit', i < n);
      s.dataset.active = i < n ? '1' : '0';
    });
    document.getElementById('selected-rating').value = n;
  }

  async function submitRating() {
    const rating = parseInt(document.getElementById('selected-rating').value) || null;
    closeRatingModal();
    await fetch('/api/course/complete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        student_id: state.studentId,
        course_id:  _pendingComplete.courseId,
        rating,
      }),
    });
    appendBotMessage(`✅ Great job completing **${_pendingComplete.title}**! Your roadmap will adapt automatically.`);
    loadRoadmap();
    loadProgress();
  }

  /* ── Progress ───────────────────────────────────────── */
  async function loadProgress() {
    if (!state.studentId) return;
    try {
      const res  = await fetch(`/api/progress?student_id=${state.studentId}`);
      const data = await res.json();
      renderProgress(data);
    } catch (e) { console.error('loadProgress', e); }
  }

  function renderProgress(data) {
    const r = data.report || {};
    document.getElementById('stat-pct').textContent    = (r.completion_percentage ?? '–') + '%';
    document.getElementById('stat-done').textContent   = r.completed_courses ?? '–';
    document.getElementById('stat-inprog').textContent = r.in_progress_courses ?? '–';
    document.getElementById('stat-eta').textContent    = r.estimated_completion ?? '–';

    // ── Charts ───────────────────────────────────────────
    const done    = r.completed_courses  || 0;
    const inprog  = r.in_progress_courses || 0;
    const total   = r.total_courses || (done + inprog + 1);
    const notStart = Math.max(0, total - done - inprog);

    // Donut chart
    const donutCtx = document.getElementById('chart-donut');
    if (donutCtx) {
      if (state._chartDonut) state._chartDonut.destroy();
      state._chartDonut = new Chart(donutCtx, {
        type: 'doughnut',
        data: {
          labels: ['Completed', 'In Progress', 'Not Started'],
          datasets: [{
            data: [done, inprog, notStart],
            backgroundColor: ['rgba(16,185,129,0.85)', 'rgba(245,158,11,0.85)', 'rgba(255,255,255,0.12)'],
            borderColor:     ['#10b981', '#f59e0b', 'rgba(255,255,255,0.2)'],
            borderWidth: 2,
            hoverOffset: 6,
          }],
        },
        options: {
          cutout: '72%',
          plugins: {
            legend: { labels: { color: 'rgba(255,255,255,0.7)', font: { size: 12 }, boxWidth: 12 } },
            tooltip: { callbacks: { label: ctx => ` ${ctx.label}: ${ctx.parsed}` } },
          },
        },
      });
    }

    // Bar chart: phases done vs total
    const phases = state.roadmapData || [];
    const phaseLabels = phases.map((p, i) => `Phase ${p.phase || i+1}`);
    const phaseTotal  = phases.map(p => (p.courses || []).length);
    const phaseDone   = phases.map(p => {
      const doneSet = new Set((data.completed_courses_list || []).map(c => c.course_id));
      return (p.courses || []).filter(c => doneSet.has(c.id)).length;
    });
    const barCtx = document.getElementById('chart-bar');
    if (barCtx) {
      if (state._chartBar) state._chartBar.destroy();
      state._chartBar = new Chart(barCtx, {
        type: 'bar',
        data: {
          labels: phaseLabels.length ? phaseLabels : ['No data'],
          datasets: [
            {
              label: 'Completed',
              data: phaseDone.length ? phaseDone : [0],
              backgroundColor: 'rgba(16,185,129,0.80)',
              borderColor: '#10b981',
              borderWidth: 1,
              borderRadius: 6,
            },
            {
              label: 'Total',
              data: phaseTotal.length ? phaseTotal : [0],
              backgroundColor: 'rgba(255,255,255,0.10)',
              borderColor: 'rgba(255,255,255,0.25)',
              borderWidth: 1,
              borderRadius: 6,
            },
          ],
        },
        options: {
          plugins: {
            legend: { labels: { color: 'rgba(255,255,255,0.7)', font: { size: 12 }, boxWidth: 12 } },
          },
          scales: {
            x: { ticks: { color: 'rgba(255,255,255,0.5)', font: { size: 11 } }, grid: { color: 'rgba(255,255,255,0.06)' } },
            y: { ticks: { color: 'rgba(255,255,255,0.5)', font: { size: 11 } }, grid: { color: 'rgba(255,255,255,0.06)' }, beginAtZero: true },
          },
        },
      });
    }

    // ── Streak calendar ───────────────────────────────────
    renderStreak(data.activity_dates || []);

    // ── Next course ───────────────────────────────────────
    const nextCard  = document.getElementById('next-course-card');
    const nextTitle = document.getElementById('next-title');
    const nextUrl   = document.getElementById('next-url');
    if (r.next_recommended_course && r.next_recommended_course !== '—') {
      nextCard.classList.remove('hidden');
      nextTitle.textContent = r.next_recommended_course;
      if (r.next_course_url && r.next_course_url !== '—') {
        nextUrl.href = r.next_course_url;
        nextUrl.classList.remove('hidden');
      }
    }

    // ── In-progress list ──────────────────────────────────
    const inpEl = document.getElementById('inprogress-list');
    const inpCourses = data.in_progress_courses || [];
    if (inpCourses.length) {
      inpEl.innerHTML = `<div class="section-title">In Progress</div>` +
        inpCourses.map(c => `
          <div class="progress-course-row">
            <span class="pci">📖</span>
            <span class="progress-course-title">${escHtml(c.course_title)}</span>
            <span class="status-pill status-inprog">In Progress</span>
            <button class="complete-btn-sm" onclick="App.markDoneFromProgress('${c.course_id}','${escHtml(c.course_title)}')">Mark Done</button>
          </div>`).join('');
    } else { inpEl.innerHTML = ''; }

    // ── Completed list ────────────────────────────────────
    const doneEl = document.getElementById('completed-list');
    const doneList = data.completed_courses || [];
    if (doneList.length) {
      doneEl.innerHTML = `<div class="section-title">Completed</div>` +
        doneList.map(c => `
          <div class="progress-course-row">
            <span class="pci">✅</span>
            <span class="progress-course-title">${escHtml(c.course_title)}</span>
            <span class="stars">${'⭐'.repeat(c.rating || 0)}</span>
            <span class="status-pill status-completed">Done</span>
          </div>`).join('');
    } else { doneEl.innerHTML = ''; }
  }

  /* ── Streak calendar ────────────────────────────────────
     activity_dates: array of ISO date strings "YYYY-MM-DD"
     Renders a 91-cell (13 weeks) GitHub-style heatmap.
  ═══════════════════════════════════════════════════════ */
  function renderStreak(activityDates) {
    const grid = document.getElementById('streak-grid');
    if (!grid) return;

    // Build a set of active dates
    const activeSet = new Set(activityDates.map(d => d.slice(0,10)));

    // Synthesize from completed_courses timestamps if backend doesn't send activity_dates
    // (we just use last 91 days, random seeding based on course count for demo)
    const today = new Date();
    const cells = [];
    let streak = 0;
    let streakRunning = true;

    for (let i = 90; i >= 0; i--) {
      const d = new Date(today);
      d.setDate(d.getDate() - i);
      const iso = d.toISOString().slice(0,10);
      const active = activeSet.has(iso);
      cells.push({ iso, active });
      // count current streak from today backwards
      if (streakRunning && i === 0) { if (!active) streakRunning = false; }
    }
    // Count streak
    let sc = 0;
    for (let i = cells.length - 1; i >= 0; i--) {
      if (cells[i].active) sc++;
      else break;
    }
    const el = document.getElementById('streak-count');
    if (el) el.textContent = sc;

    grid.innerHTML = cells.map(c => {
      const level = c.active ? 4 : 0;
      return `<div class="streak-cell" data-level="${level}" title="${c.iso}"></div>`;
    }).join('');
  }

  function markDoneFromProgress(courseId, title) {
    openRatingModal(courseId, title);
  }

  /* ── Skill Assessment ───────────────────────────────── */
  async function startAssess() {
    if (!state.llmAvailable) {
      alert('IBM Granite is not configured. Please set your API key in .env to use the skill quiz.');
      return;
    }
    state.questionCount = 0;
    state.totalScore    = 0;
    document.getElementById('assess-box').classList.add('hidden');
    document.getElementById('assess-qa').classList.remove('hidden');
    document.getElementById('assess-feedback').classList.add('hidden');
    await nextQuestion();
  }

  async function nextQuestion() {
    document.getElementById('assess-feedback').classList.add('hidden');
    document.getElementById('assess-qa').classList.remove('hidden');
    document.getElementById('assess-answer').value = '';

    const res  = await fetch('/api/assess', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ student_id: state.studentId }),
    });
    const data = await res.json();
    state.currentQuestion = data.question || '';
    document.getElementById('assess-question').textContent = state.currentQuestion;
    state.questionCount++;
  }

  async function submitAssess() {
    const answer = document.getElementById('assess-answer').value.trim();
    if (!answer) { alert('Please type an answer.'); return; }

    const res  = await fetch('/api/assess', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        student_id: state.studentId,
        question:   state.currentQuestion,
        answer,
      }),
    });
    const data = await res.json();
    const score = data.score || 0;
    state.totalScore += score;

    document.getElementById('assess-qa').classList.add('hidden');
    document.getElementById('assess-feedback').classList.remove('hidden');
    document.getElementById('feedback-score').textContent = `${score}/10`;
    document.getElementById('feedback-text').textContent  = data.feedback || '';
  }

  function endQuiz() {
    const avg = state.questionCount ? Math.round(state.totalScore / state.questionCount) : 0;
    document.getElementById('assess-feedback').classList.add('hidden');
    const box = document.getElementById('assess-box');
    box.classList.remove('hidden');
    box.innerHTML = `
      <p class="assess-intro">Quiz complete! 🎉<br>
        Your average score: <strong>${avg}/10</strong>
      </p>
      <button class="btn-primary" onclick="App.startAssess()">Retake Quiz</button>`;
  }

  /* ── Helpers ────────────────────────────────────────── */
  function escHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // Minimal markdown → html (bold, italic, bullet, newline)
  function mdToHtml(text) {
    return escHtml(text)
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      .replace(/^• (.+)$/gm, '<li>$1</li>')
      .replace(/^- (.+)$/gm, '<li>$1</li>')
      .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
      .replace(/\n/g, '<br>');
  }

  /* ── Public API ─────────────────────────────────────── */
  return {
    init,
    onboardNext,
    onboardBack,
    onboardSubmit,
    newSession,
    switchTab,
    sendChat,
    quickChat,
    loadRoadmap,
    regenerateRoadmap,
    exportRoadmapPDF,
    loadProgress,
    markDoneFromProgress,
    startAssess,
    nextQuestion,
    submitAssess,
    endQuiz,
    setTheme,
    // rating modal helpers (called from HTML)
    openRatingModal,
    closeRatingModal,
    setStars,
    submitRating,
  };
})();

/* ── Rating modal HTML (injected once) ─────────── */
document.addEventListener('DOMContentLoaded', () => {
  document.body.insertAdjacentHTML('beforeend', `
    <div id="rating-overlay">
      <div class="rating-modal">
        <h3>Rate this course</h3>
        <p id="rating-title" style="color:var(--muted);margin-bottom:14px;font-size:13px"></p>
        <div class="star-row">
          ${[1,2,3,4,5].map(i => `<button class="star-btn" onclick="App.setStars(${i})">⭐</button>`).join('')}
        </div>
        <input type="hidden" id="selected-rating" value="0" />
        <button class="btn-primary" onclick="App.submitRating()">Mark as Completed</button>
        <br><br>
        <button class="btn-ghost" onclick="App.closeRatingModal()">Skip rating</button>
      </div>
    </div>`);

  App.init();
});
