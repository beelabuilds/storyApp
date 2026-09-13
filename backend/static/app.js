/**
 * StoryApp Frontend Controller
 * Faithfully recreating frontend/src/app/index.tsx, explore.tsx, and app-tabs.tsx
 */

document.addEventListener('DOMContentLoaded', () => {
  const STORAGE_KEY = '@storyapp_saved_stories';
  const THEME_KEY = '@storyapp_theme_mode';

  // State
  let mode = localStorage.getItem(THEME_KEY) || 'light';
  let stories = loadStoriesFromStorage();
  let messages = [];
  let storyContext = { age: '4–8', dailyEvent: '', hero: '', goal: 'Just for fun' };
  let isGenerating = false;

  // Active Reader State
  let activeStory = null;
  let showFavoritesOnly = false;
  let showReviewCard = false;

  // Review Form State
  let reviewRating = 0;
  let parentLiked = null;
  let childSatisfied = null;
  let lengthFeedback = 'just_right';
  let difficultyFeedback = 'just_right';
  let improvementTags = [];
  let reviewSaved = false;

  // DOM Elements - Theme & Tabs
  const body = document.body;
  const btnToggleTheme = document.getElementById('btnToggleTheme');
  const btnToggleThemeLibrary = document.getElementById('btnToggleThemeLibrary');
  const themeIcon = document.getElementById('themeIcon');
  const themeIconLib = document.getElementById('themeIconLib');
  const btnNewChat = document.getElementById('btnNewChat');

  const tabNavAssistant = document.getElementById('tabNavAssistant');
  const tabNavBookshelf = document.getElementById('tabNavBookshelf');
  const screenChat = document.getElementById('screenChat');
  const screenBookshelf = document.getElementById('screenBookshelf');

  // DOM Elements - Chat Screen
  const messagesContainer = document.getElementById('messagesContainer');
  const emptyWelcomeBanner = document.getElementById('emptyWelcomeBanner');
  const thinkingIndicator = document.getElementById('thinkingIndicator');
  const chatScrollArea = document.getElementById('chatScrollArea');
  const chatInput = document.getElementById('chatInput');
  const btnSendMessage = document.getElementById('btnSendMessage');

  // DOM Elements - Bookshelf Screen
  const bookshelfLibraryView = document.getElementById('bookshelfLibraryView');
  const bookshelfReaderView = document.getElementById('bookshelfReaderView');
  const booksGrid = document.getElementById('booksGrid');
  const emptyBookshelfState = document.getElementById('emptyBookshelfState');
  const btnEmptyCreate = document.getElementById('btnEmptyCreate');
  const btnFilterAll = document.getElementById('btnFilterAll');
  const btnFilterFavorites = document.getElementById('btnFilterFavorites');

  // DOM Elements - Reader View
  const btnBackToLibrary = document.getElementById('btnBackToLibrary');
  const btnReaderFavorite = document.getElementById('btnReaderFavorite');
  const readerFavIcon = document.getElementById('readerFavIcon');
  const readerTitle = document.getElementById('readerTitle');
  const readerMeta = document.getElementById('readerMeta');
  const readerStoryBody = document.getElementById('readerStoryBody');
  const readerFallbackBadge = document.getElementById('readerFallbackBadge');
  const btnReaderActionFavorite = document.getElementById('btnReaderActionFavorite');
  const btnToggleReviewCard = document.getElementById('btnToggleReviewCard');

  // DOM Elements - Review Card
  const readerReviewCard = document.getElementById('readerReviewCard');
  const ratingRow = document.getElementById('ratingRow');
  const parentLikedRow = document.getElementById('parentLikedRow');
  const childSatisfiedRow = document.getElementById('childSatisfiedRow');
  const lengthFeedbackRow = document.getElementById('lengthFeedbackRow');
  const difficultyFeedbackRow = document.getElementById('difficultyFeedbackRow');
  const improvementTagsRow = document.getElementById('improvementTagsRow');
  const reviewCommentInput = document.getElementById('reviewCommentInput');
  const reviewErrorMsg = document.getElementById('reviewErrorMsg');
  const reviewSuccessMsg = document.getElementById('reviewSuccessMsg');
  const btnSaveReview = document.getElementById('btnSaveReview');

  // ========================================================
  // THEME MANAGEMENT (Light / Dark)
  // ========================================================
  function applyTheme(newMode) {
    mode = newMode;
    localStorage.setItem(THEME_KEY, mode);
    body.className = mode === 'dark' ? 'theme-dark' : 'theme-light';
    const iconChar = mode === 'dark' ? '☀' : '☾';
    if (themeIcon) themeIcon.textContent = iconChar;
    if (themeIconLib) themeIconLib.textContent = iconChar;
  }

  function toggleTheme() {
    applyTheme(mode === 'dark' ? 'light' : 'dark');
  }

  btnToggleTheme?.addEventListener('click', toggleTheme);
  btnToggleThemeLibrary?.addEventListener('click', toggleTheme);
  applyTheme(mode);

  // ========================================================
  // STORAGE HELPERS (from use-local-stories.ts)
  // ========================================================
  function loadStoriesFromStorage() {
    try {
      const data = localStorage.getItem(STORAGE_KEY);
      return data ? JSON.parse(data) : [];
    } catch (e) {
      console.warn('Storage read error:', e);
      return [];
    }
  }

  function saveStoriesToStorage(updatedStories) {
    stories = updatedStories;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(stories));
    } catch (e) {
      console.warn('Storage write error:', e);
    }
    renderBookshelf();
  }

  function getReadingDuration(text, age) {
    if (!text) return '3–5 min read';
    const words = text.trim().split(/\s+/).filter(Boolean).length;
    const ageStr = String(age || '').trim().toLowerCase();

    if (ageStr.includes('8') && !ageStr.includes('6-8') && !ageStr.includes('4-8')) return '7–10 min read';
    if (ageStr.includes('7') && !ageStr.includes('6-8')) return '6–8 min read';
    if (ageStr.includes('6-8') || ageStr.includes('6')) return words >= 600 ? '6–8 min read' : '5–7 min read';
    if (ageStr.includes('5')) return '4–6 min read';
    if (ageStr.includes('4')) return '3–5 min read';

    if (words >= 650) return '7–10 min read';
    if (words >= 550) return '6–8 min read';
    if (words >= 450) return '5–7 min read';
    if (words >= 350) return '4–6 min read';
    return '3–5 min read';
  }

  // ========================================================
  // NAVIGATION TABS (from app-tabs.tsx)
  // ========================================================
  function switchTab(tab) {
    if (tab === 'assistant') {
      tabNavAssistant.classList.add('active');
      tabNavBookshelf.classList.remove('active');
      screenChat.classList.add('active');
      screenBookshelf.classList.remove('active');
    } else {
      tabNavBookshelf.classList.add('active');
      tabNavAssistant.classList.remove('active');
      screenBookshelf.classList.add('active');
      screenChat.classList.remove('active');
      renderBookshelf();
    }
  }

  tabNavAssistant.addEventListener('click', () => switchTab('assistant'));
  tabNavBookshelf.addEventListener('click', () => switchTab('bookshelf'));
  btnEmptyCreate.addEventListener('click', () => switchTab('assistant'));

  // ========================================================
  // CHAT SYSTEM (from index.tsx)
  // ========================================================
  const defaultSuggestions = [
    'Bedtime story',
    'Something happened today',
    'Help with a fear',
    'Build confidence',
    'Teach kindness',
    'Just for fun'
  ];

  function initChat() {
    messages = [{
      id: 'welcome',
      role: 'assistant',
      text: "Hi! What kind of story would you like to create for your child today?",
      chips: defaultSuggestions.slice(0, 4)
    }];
    storyContext = { age: '4–8', dailyEvent: '', hero: '', goal: 'Just for fun' };
    renderMessages();
  }

  btnNewChat.addEventListener('click', () => {
    initChat();
  });

  function renderMessages() {
    messagesContainer.innerHTML = '';

    if (messages.length <= 1) {
      emptyWelcomeBanner.classList.remove('hidden');
    } else {
      emptyWelcomeBanner.classList.add('hidden');
    }

    messages.forEach((msg, index) => {
      const isLatestAssistant = msg.role === 'assistant' && index === messages.length - 1;
      const block = document.createElement('div');
      block.className = `message-block ${msg.role === 'user' ? 'user-block' : ''}`;

      if (msg.role === 'user') {
        const bubble = document.createElement('div');
        bubble.className = 'user-bubble';
        bubble.textContent = msg.text;
        block.appendChild(bubble);
      } else {
        const textEl = document.createElement('div');
        textEl.className = 'assistant-text';
        textEl.textContent = msg.text;
        block.appendChild(textEl);

        // Story Card if attached
        if (msg.story) {
          const card = createStoryCardElement(msg.story, msg.id);
          block.appendChild(card);
        }

        // Suggestion Chips if latest assistant message
        if (isLatestAssistant && msg.chips && msg.chips.length > 0 && !isGenerating) {
          const chipsGroup = document.createElement('div');
          chipsGroup.className = 'chips-group';
          msg.chips.forEach((chipText) => {
            const chipBtn = document.createElement('button');
            chipBtn.type = 'button';
            chipBtn.className = 'chip';
            chipBtn.textContent = chipText;
            chipBtn.addEventListener('click', () => handleChipPress(chipText));
            chipsGroup.appendChild(chipBtn);
          });
          block.appendChild(chipsGroup);
        }
      }

      messagesContainer.appendChild(block);
    });

    chatScrollArea.scrollTop = chatScrollArea.scrollHeight;
  }

  function sanitizeStoryTitle(title, character) {
    let t = (title || '').trim();
    t = t.replace(/^(?:\*{1,3}|#{1,6})?\s*title\s*:\s*/i, '').trim();
    t = t.replace(/^[*#"'_]+|[*#"'_]+$/g, '').trim();
    if (!t || /your creative title|creative title|story title/i.test(t) || t.startsWith('[')) {
      if (character && !['explorer', 'a friendly explorer', 'my child', 'none'].includes(character.toLowerCase())) {
        return `${character}'s Bedtime Adventure`;
      }
      return 'Barnaby the Bear and the Whispering Night';
    }
    return t;
  }

  function createStoryCardElement(story, messageId) {
    const card = document.createElement('div');
    card.className = 'story-card';

    const eyebrow = document.createElement('div');
    eyebrow.className = 'story-eyebrow';
    eyebrow.textContent = `A STORY ABOUT ${String(story.character || 'BARNABY THE BEAR').toUpperCase()}`;
    card.appendChild(eyebrow);

    const titleEl = document.createElement('h3');
    titleEl.className = 'story-title';
    titleEl.textContent = sanitizeStoryTitle(story.title, story.character);
    card.appendChild(titleEl);


    const preview = document.createElement('div');
    preview.className = 'story-preview';
    preview.textContent = story.story;
    card.appendChild(preview);

    const actions = document.createElement('div');
    actions.className = 'story-actions';

    const readBtn = document.createElement('button');
    readBtn.type = 'button';
    readBtn.className = 'read-button';
    readBtn.textContent = 'Read full story';
    readBtn.addEventListener('click', () => handleReadStory(story));
    actions.appendChild(readBtn);

    const bookmarkBtn = document.createElement('button');
    bookmarkBtn.type = 'button';
    bookmarkBtn.className = `bookmark-button ${story.isFavorite ? 'active' : ''}`;
    bookmarkBtn.textContent = story.isFavorite ? '♥' : '♡';
    bookmarkBtn.addEventListener('click', () => handleToggleStoryBookmark(story, messageId));
    actions.appendChild(bookmarkBtn);

    card.appendChild(actions);
    return card;
  }

  function handleChipPress(chip) {
    const currentTyped = chatInput.value.trim();
    if (currentTyped) {
      submitMessage(`${chip}: ${currentTyped}`);
    } else {
      submitMessage(chip);
    }
  }

  async function submitMessage(rawText) {
    const text = rawText.trim();
    if (!text || isGenerating) return;

    chatInput.value = '';
    const userMsg = { id: `user-${Date.now()}`, role: 'user', text };
    messages.push(userMsg);
    renderMessages();

    // Call /chat endpoint
    isGenerating = true;
    thinkingIndicator.classList.remove('hidden');
    btnSendMessage.disabled = true;

    try {
      const response = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: messages.map(({ role, text }) => ({ role, content: text })),
          storyContext: storyContext,
        }),
      });

      if (!response.ok) {
        const errorJson = await response.json().catch(() => ({}));
        throw new Error(errorJson.detail || `Server returned status ${response.status}`);
      }

      const data = await response.json();
      storyContext = { ...storyContext, ...(data.storyContext || {}) };

      let attachedStory = null;
      if (data.story) {
        const storyText = typeof data.story === 'string'
          ? data.story
          : (data.story.content || data.story.story || '');
        const storyTitle = (typeof data.story === 'object' && data.story?.title)
          ? data.story.title
          : 'A New Adventure';

        if (storyText) {
          attachedStory = {
            id: `story-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
            title: storyTitle,
            story: storyText,
            event: String(storyContext.dailyEvent || ''),
            goal: String(storyContext.goal || 'Just for fun'),
            character: String((data.story && data.story.character) || storyContext.hero || 'Story Friend'),
            age: String(storyContext.age || '4-8'),
            createdAt: new Date().toISOString(),
            emoji: '',
            isFavorite: false,
            readingProgress: 0,
            is_fallback: Boolean(data.is_fallback),
          };

          // Save to local storage
          const existing = loadStoriesFromStorage();
          saveStoriesToStorage([attachedStory, ...existing]);
        }
      }

      messages.push({
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        text: data.assistantMessage || 'Here is a story created for your child',
        chips: data.suggestions || defaultSuggestions.slice(0, 4),
        story: attachedStory,
      });
    } catch (err) {
      console.error('Chat error:', err);
      messages.push({
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        text: `⚠️ Model Error: ${err.message || 'Could not reach the story engine.'}`,
        chips: defaultSuggestions.slice(0, 3),
      });
    } finally {
      isGenerating = false;
      thinkingIndicator.classList.add('hidden');
      btnSendMessage.disabled = false;
      renderMessages();
    }
  }

  btnSendMessage.addEventListener('click', () => submitMessage(chatInput.value));
  chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submitMessage(chatInput.value);
    }
  });

  function handleReadStory(story) {
    // Open reader in Bookshelf screen
    switchTab('bookshelf');
    openReader(story);
  }

  function handleToggleStoryBookmark(story, messageId) {
    const updated = !story.isFavorite;
    story.isFavorite = updated;

    // Update in stored stories
    const updatedStories = stories.map((s) => s.id === story.id ? { ...s, isFavorite: updated } : s);
    saveStoriesToStorage(updatedStories);

    // Update in message
    messages = messages.map((m) => {
      if (m.id === messageId && m.story) {
        return { ...m, story: { ...m.story, isFavorite: updated } };
      }
      return m;
    });
    renderMessages();
  }

  // ========================================================
  // BOOKSHELF & LIBRARY (from explore.tsx)
  // ========================================================
  function renderBookshelf() {
    if (activeStory) {
      bookshelfLibraryView.classList.add('hidden');
      bookshelfReaderView.classList.remove('hidden');
      return;
    }

    bookshelfReaderView.classList.add('hidden');
    bookshelfLibraryView.classList.remove('hidden');

    const filtered = showFavoritesOnly ? stories.filter((s) => s.isFavorite) : stories;

    if (stories.length === 0) {
      booksGrid.innerHTML = '';
      emptyBookshelfState.classList.remove('hidden');
      emptyBookshelfState.querySelector('.empty-emoji').textContent = '';
      emptyBookshelfState.querySelector('.empty-title').textContent = 'Your bookshelf is empty';
      emptyBookshelfState.querySelector('.empty-subtitle').textContent = 'Your first adventure is waiting.';
      btnEmptyCreate.classList.remove('hidden');
      return;
    }

    if (filtered.length === 0 && showFavoritesOnly) {
      booksGrid.innerHTML = '';
      emptyBookshelfState.classList.remove('hidden');
      emptyBookshelfState.querySelector('.empty-emoji').textContent = '♡';
      emptyBookshelfState.querySelector('.empty-title').textContent = 'No favorites yet ♥';
      emptyBookshelfState.querySelector('.empty-subtitle').textContent = 'Tap the heart on any story to save it here.';
      btnEmptyCreate.classList.add('hidden');
      return;
    }

    emptyBookshelfState.classList.add('hidden');
    booksGrid.innerHTML = '';

    filtered.forEach((story) => {
      const card = document.createElement('div');
      card.className = 'book-card';
      card.addEventListener('click', (e) => {
        if (e.target.closest('.favorite-text') || e.target.closest('.delete-story')) return;
        openReader(story);
      });

      const cover = document.createElement('div');
      cover.className = 'book-cover';
      cover.innerHTML = `<span class="book-emoji">${story.emoji || ''}</span><span class="cover-label">STORY</span>`;
      card.appendChild(cover);

      const cardRow = document.createElement('div');
      cardRow.className = 'card-row';

      const titleEl = document.createElement('span');
      titleEl.className = 'book-title';
      titleEl.textContent = sanitizeStoryTitle(story.title, story.character);
      cardRow.appendChild(titleEl);

      const fav = document.createElement('span');
      fav.className = `favorite-text ${story.isFavorite ? 'is-fav' : ''}`;
      fav.textContent = story.isFavorite ? '♥' : '♡';
      fav.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleStoryFavorite(story.id);
      });
      cardRow.appendChild(fav);

      const deleteBtn = document.createElement('button');
      deleteBtn.type = 'button';
      deleteBtn.className = 'delete-story';
      deleteBtn.innerHTML = '🗑';
      deleteBtn.addEventListener('click', (e) => {
        e.stopPropagation();

        const confirmed = confirm('Delete this saved story?');
        if (!confirmed) return;

        deleteStory(story.id);
      });

      cardRow.appendChild(deleteBtn);
      card.appendChild(cardRow);

      const dateEl = document.createElement('div');
      dateEl.className = 'story-meta';
      dateEl.textContent = new Date(story.createdAt || Date.now()).toLocaleDateString();
      card.appendChild(dateEl);

      booksGrid.appendChild(card);
    });
  }

  btnFilterAll.addEventListener('click', () => {
    showFavoritesOnly = false;
    btnFilterAll.classList.add('active');
    btnFilterFavorites.classList.remove('active');
    renderBookshelf();
  });

  btnFilterFavorites.addEventListener('click', () => {
    showFavoritesOnly = true;
    btnFilterFavorites.classList.add('active');
    btnFilterAll.classList.remove('active');
    renderBookshelf();
  });

  function toggleStoryFavorite(id) {
    const updated = stories.map((s) => s.id === id ? { ...s, isFavorite: !s.isFavorite } : s);
    saveStoriesToStorage(updated);
    if (activeStory && activeStory.id === id) {
      activeStory = updated.find((s) => s.id === id) || null;
      updateReaderFavoriteUI();
    }
  }

  function deleteStory(id) {
    const updated = stories.filter((story) => story.id !== id);
    saveStoriesToStorage(updated);

    if (activeStory && activeStory.id === id) {
      activeStory = null;
    }

    renderBookshelf();
  }

  // ========================================================
  // READER VIEW & PARENT REVIEWS (from explore.tsx)
  // ========================================================
  function applyReviewToForm(r) {
    if (!r) {
      reviewRating = 0;
      parentLiked = null;
      childSatisfied = null;
      lengthFeedback = 'just_right';
      difficultyFeedback = 'just_right';
      improvementTags = [];
      reviewCommentInput.value = '';
      btnToggleReviewCard.textContent = 'Review this story';
      renderReviewFormInputs();
      return;
    }

    reviewRating = Number(r.rating) || 0;

    // Normalize parentLiked: handle boolean, int (1/0), string ('true'/'false')
    const rawLiked = (r.parentLiked !== undefined) ? r.parentLiked : r.parent_liked;
    if (rawLiked === true || rawLiked === 'true' || rawLiked === 1 || rawLiked === '1') {
      parentLiked = true;
    } else if (rawLiked === false || rawLiked === 'false' || rawLiked === 0 || rawLiked === '0') {
      parentLiked = false;
    } else {
      parentLiked = null;
    }

    // Normalize childSatisfied: handle 'yes', 'a_little', 'no', or boolean
    let rawChild = (r.childSatisfied !== undefined) ? r.childSatisfied : r.child_satisfied;
    if (rawChild === true) rawChild = 'yes';
    else if (rawChild === false) rawChild = 'no';
    childSatisfied = rawChild ? String(rawChild).trim() : null;

    lengthFeedback = (r.lengthFeedback || r.length_feedback || 'just_right').trim();
    difficultyFeedback = (r.difficultyFeedback || r.difficulty_feedback || 'just_right').trim();

    // Normalize improvementTags: handle array or JSON string
    let rawTags = (r.improvementTags !== undefined) ? r.improvementTags : r.improvement_tags;
    if (typeof rawTags === 'string') {
      try { rawTags = JSON.parse(rawTags); } catch (e) { rawTags = []; }
    }
    improvementTags = Array.isArray(rawTags) ? [...rawTags] : [];

    reviewCommentInput.value = r.comment || r.feedback || '';
    btnToggleReviewCard.textContent = reviewRating > 0
      ? `Edit parent review (★ ${reviewRating}/10)`
      : 'Edit parent review';

    renderReviewFormInputs();
  }

  function openReader(story) {
    activeStory = story;
    const cleanTitle = sanitizeStoryTitle(story.title, story.character);
    readerTitle.textContent = cleanTitle;

    if (story.is_fallback) {
      readerFallbackBadge.classList.remove('hidden');
    } else {
      readerFallbackBadge.classList.add('hidden');
    }

    readerStoryBody.innerHTML = '';
    const storyText = story.content || story.story || '';
    const paragraphs = storyText.split(/\n\s*\n+/).map((p) => p.trim()).filter(Boolean);
    const normalizedTitle = cleanTitle.toLowerCase().replace(/[^a-z0-9]/g, '');
    const seenParagraphs = new Set();

    paragraphs.forEach((p) => {
      const lower = p.toLowerCase();
      // Drop any line with [Your Creative Title] or placeholder
      if (lower.includes('your creative title') || lower.includes('[creative title]') || lower.includes('[story title]')) {
        return;
      }
      // Drop any line starting with Title:
      if (/^(?:\*{1,3}|#{1,6})?\s*title\s*:/i.test(p)) {
        return;
      }
      // Drop duplicate of the title header
      const normP = lower.replace(/[^a-z0-9]/g, '');
      if (normalizedTitle && (normP === normalizedTitle || normP === `title${normalizedTitle}`)) {
        return;
      }
      // Drop duplicate paragraphs
      if (seenParagraphs.has(normP)) {
        return;
      }
      // Drop near-duplicate paragraphs (prefix match)
      if (normP.length > 30) {
        const prefix = normP.slice(0, 30);
        for (const seen of seenParagraphs) {
          if (seen.length > 30 && (seen.includes(prefix) || prefix.includes(seen.slice(0, 30)))) {
            return;
          }
        }
      }
      seenParagraphs.add(normP);

      const pEl = document.createElement('p');
      pEl.textContent = p;
      readerStoryBody.appendChild(pEl);
    });

    updateReaderFavoriteUI();

    // 1. Populate review immediately from cached/stored story object
    applyReviewToForm(story.review);

    // 2. Fetch fresh review from SQLite database if story has an ID
    if (story.id) {
      fetch(`/reviews/${encodeURIComponent(story.id)}`)
        .then((res) => {
          if (res.ok) return res.json();
          return null;
        })
        .then((dbReview) => {
          if (dbReview && activeStory && activeStory.id === story.id) {
            activeStory.review = dbReview;
            applyReviewToForm(dbReview);
            const currentList = loadStoriesFromStorage();
            const updated = currentList.map((s) => s.id === story.id ? { ...s, review: dbReview } : s);
            saveStoriesToStorage(updated);
          }
        })
        .catch((err) => console.log('Background review sync notice:', err));
    }

    readerReviewCard.classList.add('hidden');
    showReviewCard = false;

    bookshelfLibraryView.classList.add('hidden');
    bookshelfReaderView.classList.remove('hidden');
  }

  btnBackToLibrary.addEventListener('click', () => {
    activeStory = null;
    bookshelfReaderView.classList.add('hidden');
    bookshelfLibraryView.classList.remove('hidden');
    renderBookshelf();
  });

  function updateReaderFavoriteUI() {
    if (!activeStory) return;
    const isFav = activeStory.isFavorite;
    readerFavIcon.textContent = isFav ? '♥' : '♡';
    readerFavIcon.style.color = isFav ? '#FF4D6D' : '';
    btnReaderActionFavorite.textContent = isFav ? '♥ Favorited' : '♡ Add to Favorites';
  }

  btnReaderFavorite.addEventListener('click', () => {
    if (activeStory) toggleStoryFavorite(activeStory.id);
  });

  btnReaderActionFavorite.addEventListener('click', () => {
    if (activeStory) toggleStoryFavorite(activeStory.id);
  });

  btnToggleReviewCard.addEventListener('click', () => {
    showReviewCard = !showReviewCard;
    if (showReviewCard) {
      renderReviewFormInputs();
      readerReviewCard.classList.remove('hidden');
      readerReviewCard.scrollIntoView({ behavior: 'smooth' });
    } else {
      readerReviewCard.classList.add('hidden');
    }
  });

  // Setup Review Rating Buttons (1 to 10)
  function initRatingButtons() {
    ratingRow.innerHTML = '';
    for (let i = 1; i <= 10; i++) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'rating-btn';
      btn.textContent = i;
      btn.addEventListener('click', () => {
        reviewRating = i;
        renderReviewFormInputs();
      });
      ratingRow.appendChild(btn);
    }
  }
  initRatingButtons();

  // Setup Option Buttons (Liked, Satisfied, Length, Difficulty)
  function setupOptionGroup(container, getter, setter) {
    container.querySelectorAll('.option-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        const val = btn.getAttribute('data-val');
        setter(val === 'true' ? true : val === 'false' ? false : val);
        renderReviewFormInputs();
      });
    });
  }

  setupOptionGroup(parentLikedRow, () => parentLiked, (v) => { parentLiked = v; });
  setupOptionGroup(childSatisfiedRow, () => childSatisfied, (v) => { childSatisfied = v; });
  setupOptionGroup(lengthFeedbackRow, () => lengthFeedback, (v) => { lengthFeedback = v; });
  setupOptionGroup(difficultyFeedbackRow, () => difficultyFeedback, (v) => { difficultyFeedback = v; });

  // Improvement Tag Buttons
  improvementTagsRow.querySelectorAll('.tag-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const tag = btn.getAttribute('data-tag');
      const idx = improvementTags.findIndex((t) => t.toLowerCase() === tag.toLowerCase());
      if (idx >= 0) {
        improvementTags.splice(idx, 1);
      } else {
        improvementTags.push(tag);
      }
      renderReviewFormInputs();
    });
  });

  function renderReviewFormInputs() {
    // Ratings (1 to 10)
    ratingRow.querySelectorAll('.rating-btn').forEach((btn, idx) => {
      btn.classList.toggle('active', (idx + 1) === reviewRating);
    });

    // Parent liked (Yes / Not really)
    parentLikedRow.querySelectorAll('.option-btn').forEach((btn) => {
      const isYesBtn = btn.getAttribute('data-val') === 'true';
      const shouldBeActive = (parentLiked === true && isYesBtn) || (parentLiked === false && !isYesBtn);
      btn.classList.toggle('active', Boolean(shouldBeActive));
    });

    // Child satisfied (Yes / A little / No)
    childSatisfiedRow.querySelectorAll('.option-btn').forEach((btn) => {
      btn.classList.toggle('active', btn.getAttribute('data-val') === childSatisfied);
    });

    // Length (Too short / Just right / Too long)
    lengthFeedbackRow.querySelectorAll('.option-btn').forEach((btn) => {
      btn.classList.toggle('active', btn.getAttribute('data-val') === lengthFeedback);
    });

    // Difficulty (Too easy / Just right / Too difficult)
    difficultyFeedbackRow.querySelectorAll('.option-btn').forEach((btn) => {
      btn.classList.toggle('active', btn.getAttribute('data-val') === difficultyFeedback);
    });

    // Improvement tags (case-insensitive check)
    improvementTagsRow.querySelectorAll('.tag-btn').forEach((btn) => {
      const tag = (btn.getAttribute('data-tag') || '').trim().toLowerCase();
      const isSelected = improvementTags.some((t) => String(t).trim().toLowerCase() === tag);
      btn.classList.toggle('active', isSelected);
    });

    reviewErrorMsg.classList.add('hidden');
    reviewSuccessMsg.classList.add('hidden');
  }

  // Save Review to SQLite via FastAPI /reviews
  btnSaveReview.addEventListener('click', async () => {
    if (!activeStory) return;

    if (reviewRating < 1) {
      reviewErrorMsg.textContent = 'Please rate the story from 1 to 10.';
      reviewErrorMsg.classList.remove('hidden');
      return;
    }

    if (parentLiked === null) {
      reviewErrorMsg.textContent = 'Please tell us whether you liked the story.';
      reviewErrorMsg.classList.remove('hidden');
      return;
    }

    if (childSatisfied === null) {
      reviewErrorMsg.textContent = 'Please tell us whether your child enjoyed the story.';
      reviewErrorMsg.classList.remove('hidden');
      return;
    }

    reviewErrorMsg.classList.add('hidden');
    btnSaveReview.disabled = true;
    btnSaveReview.textContent = 'Saving...';

    const reviewObj = {
      storyId: activeStory.id,
      storyTitle: activeStory.title,
      age: activeStory.age || '4-8',
      rating: reviewRating,
      parentLiked: parentLiked,
      childSatisfied: childSatisfied,
      lengthFeedback: lengthFeedback,
      difficultyFeedback: difficultyFeedback,
      improvementTags: [...improvementTags],
      comment: reviewCommentInput.value.trim(),
      updatedAt: new Date().toISOString(),
    };

    // 1. Save locally in story object
    const updatedStory = { ...activeStory, review: reviewObj };
    activeStory = updatedStory;
    const updatedList = stories.map((s) => s.id === updatedStory.id ? updatedStory : s);
    saveStoriesToStorage(updatedList);

    // 2. Save into SQLite database via FastAPI
    try {
      const res = await fetch('/reviews', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          storyId: activeStory.id,
          storyTitle: activeStory.title,
          age: activeStory.age || '4-8',
          rating: reviewRating,
          parentLiked: parentLiked,
          childSatisfied: childSatisfied,
          lengthFeedback: lengthFeedback,
          difficultyFeedback: difficultyFeedback,
          improvementTags: improvementTags,
          comment: reviewCommentInput.value.trim(),
        }),
      });

      if (!res.ok) {
        throw new Error('Database returned ' + res.status);
      }

      btnToggleReviewCard.textContent = `Edit parent review (★ ${reviewRating}/10)`;
      reviewSuccessMsg.classList.remove('hidden');
      renderReviewFormInputs();
    } catch (e) {
      console.warn('SQLite review save error:', e);
      reviewErrorMsg.textContent = 'Saved locally, but could not reach SQLite database.';
      reviewErrorMsg.classList.remove('hidden');
    } finally {
      btnSaveReview.disabled = false;
      btnSaveReview.textContent = 'Save Review';
    }
  });

  // Start chat session
  initChat();
});

