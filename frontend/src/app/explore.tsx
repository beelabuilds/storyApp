import { useEffect, useState } from 'react';
import { Alert, Platform, Pressable, ScrollView, StyleSheet, TextInput, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { BottomTabInset, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';
import { Story, useLocalStories } from '@/hooks/use-local-stories';
import { getApiUrl, getReadingDuration } from '@/app/index';

export default function ExploreScreen() {
  const theme = useTheme();
  const router = useRouter();
  const safeAreaInsets = useSafeAreaInsets();
  const { storyId } = useLocalSearchParams<{ storyId?: string }>();
  const { stories, loading, deleteStory, clearAllStories, refreshStories, toggleFavorite, saveStoryReview } = useLocalStories();
  const [activeStory, setActiveStory] = useState<Story | null>(null);
  const [showFavorites, setShowFavorites] = useState(false);

  const [showReview, setShowReview] = useState(false);
  const [rating, setRating] = useState(0);
  const [parentLiked, setParentLiked] = useState<boolean | null>(null);
  const [childSatisfied, setChildSatisfied] =
    useState<'yes' | 'a_little' | 'no' | null>(null);

  const [lengthFeedback, setLengthFeedback] =
    useState<'too_short' | 'just_right' | 'too_long' | null>(null);

  const [difficultyFeedback, setDifficultyFeedback] =
    useState<'too_easy' | 'just_right' | 'too_difficult' | null>(null);

  const [improvementTags, setImprovementTags] = useState<string[]>([]);
  const [comment, setComment] = useState('');
  const [reviewSaved, setReviewSaved] = useState(false);
  const [reviewError, setReviewError] = useState('');

  useEffect(() => { refreshStories(); }, []);
  useEffect(() => {
    if (storyId) setActiveStory(stories.find((story) => story.id === storyId) ?? null);
  }, [stories, storyId]);

  useEffect(() => {
    const review = activeStory?.review;

    if (!review) {
      setRating(0);
      setParentLiked(null);
      setChildSatisfied(null);
      setLengthFeedback(null);
      setDifficultyFeedback(null);
      setImprovementTags([]);
      setComment('');
      setReviewSaved(false);
      return;
    }

    setRating(review.rating);
    setParentLiked(review.parentLiked);
    setChildSatisfied(review.childSatisfied);
    setLengthFeedback(review.lengthFeedback);
    setDifficultyFeedback(review.difficultyFeedback);
    setImprovementTags(review.improvementTags ?? []);
    setComment(review.comment ?? '');
    setReviewSaved(true);
    setShowReview(true);
  }, [activeStory?.id, activeStory?.review?.updatedAt]);

  const confirmDelete = (id: string, title: string) => {
    const remove = () => { deleteStory(id); setActiveStory(null); };
    if (Platform.OS === 'web') {
      if (window.confirm(`Delete "${title}" from your bookshelf?`)) remove();
    } else {
      Alert.alert('Delete Story', `Delete "${title}" from your bookshelf?`, [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Delete', style: 'destructive', onPress: remove },
      ]);
    }
  };

  const confirmClear = () => {
    const remove = () => clearAllStories();
    if (Platform.OS === 'web') {
      if (window.confirm('Delete every story from your bookshelf?')) remove();
    } else {
      Alert.alert('Clear Bookshelf', 'Delete every story from your bookshelf?', [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Clear All', style: 'destructive', onPress: remove },
      ]);
    }
  };

  const filteredStories = showFavorites ? stories.filter((story) => story.isFavorite) : stories;
  const bottomPadding = Math.max(safeAreaInsets.bottom, 16) + BottomTabInset + 48;
  const handleToggleFavorite = async (id: string) => {
    const updatedStory = await toggleFavorite(id);
    if (updatedStory && activeStory?.id === id) setActiveStory(updatedStory);
  };

  const improvementOptions = [
    'Funnier',
    'More adventure',
    'More animals',
    'Less scary',
    'Longer',
    'Shorter',
  ];

  const toggleImprovementTag = (tag: string) => {
    setImprovementTags((current) =>
      current.includes(tag)
        ? current.filter((item) => item !== tag)
        : [...current, tag]
    );
    setReviewSaved(false);
  };

  const handleSaveReview = async () => {
    if (!activeStory) return;

    if (rating < 1) {
      setReviewError('Please rate the story from 1 to 10.');
      return;
    }

    if (parentLiked === null) {
      setReviewError('Please tell us whether you liked the story.');
      return;
    }

    if (childSatisfied === null) {
      setReviewError('Please tell us whether your child enjoyed the story.');
      return;
    }

    setReviewError('');

    // Save review locally first
    const updated = await saveStoryReview(activeStory.id, {
      rating,
      parentLiked,
      childSatisfied,
      lengthFeedback,
      difficultyFeedback,
      improvementTags,
      comment: comment.trim(),
    });

    if (!updated) {
      setReviewError('Could not save the review on this device.');
      return;
    }

    setActiveStory(updated);

    // Save the same review in SQLite through FastAPI
    try {
      const baseUrl = getApiUrl();

      const response = await fetch(`${baseUrl}/reviews`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          storyId: activeStory.id,
          storyTitle: activeStory.title,
          age: activeStory.age,
          rating,
          parentLiked,
          childSatisfied,
          lengthFeedback,
          difficultyFeedback,
          improvementTags,
          comment: comment.trim(),
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || 'Database request failed.');
      }

      setReviewSaved(true);
      setReviewError('');
    } catch (error) {
      console.error('Failed to save review to database:', error);

      setReviewSaved(false);
      setReviewError(
        'Review was saved on this device, but could not be saved to the database.'
      );
    }
  };

  if (activeStory) {
    return (
      <ThemedView style={styles.container}>
        <ScrollView contentContainerStyle={[styles.readerContent, { paddingBottom: bottomPadding }]} showsVerticalScrollIndicator={false}>
          <View style={styles.readerToolbar}>
            <Pressable onPress={() => { setActiveStory(null); router.navigate('/explore'); }} style={[styles.toolButton, { backgroundColor: theme.surfaceElevated, borderColor: theme.border, borderWidth: 1 }]}>
              <ThemedText style={{ color: theme.textPrimary, fontWeight: '700' }}>← Back to Stories</ThemedText>
            </Pressable>
            <View style={styles.toolbarActions}>
              <Pressable onPress={() => handleToggleFavorite(activeStory.id)} style={[styles.toolButton, { backgroundColor: theme.surfaceElevated, borderColor: theme.border, borderWidth: 1 }]}>
                <ThemedText style={[styles.favoriteText, { color: activeStory.isFavorite ? '#FF4D6D' : theme.textSecondary }]}>
                  {activeStory.isFavorite ? '♥' : '♡'}
                </ThemedText>
              </Pressable>

          

              <Pressable onPress={() => confirmDelete(activeStory.id, activeStory.title)} style={[styles.toolButton, { backgroundColor: theme.surfaceElevated, borderColor: theme.border, borderWidth: 1 }]}>
                <ThemedText style={{ color: theme.textPrimary, fontWeight: '800' }}>•••</ThemedText>
              </Pressable>
            </View>
          </View>
          <ThemedText style={[styles.readerTitle, { color: theme.textPrimary }]}>{activeStory.title}</ThemedText>
          <ThemedText themeColor="textSecondary" style={styles.readerMeta}>
            Ages {activeStory.age} • {activeStory.character} • ⏱ {getReadingDuration(activeStory.story, activeStory.age)}
          </ThemedText>
          <View style={[styles.divider, { backgroundColor: theme.accent }]} />
          <ThemedText style={[styles.readerStory, { color: theme.textPrimary }]}>{activeStory.story}</ThemedText>
          <Pressable onPress={() => handleToggleFavorite(activeStory.id)} style={[styles.readerAction, { backgroundColor: theme.accent }]}>
            <ThemedText style={{ color: theme.accentText, fontWeight: '800', fontSize: 16 }}>
              {activeStory.isFavorite ? '♥ Favorited' : '♡ Add to Favorites'}
            </ThemedText>
          </Pressable>

          <Pressable
            onPress={() => setShowReview((current) => !current)}
            style={[
              styles.reviewToggle,
              {
                backgroundColor: theme.surfaceElevated,
                borderColor: theme.border,
              },
            ]}
          >
            <ThemedText
              style={{
                color: theme.textPrimary,
                fontWeight: '800',
                fontSize: 16,
              }}
            >
              {activeStory.review ? 'Edit parent review' : 'Review this story'}
            </ThemedText>
          </Pressable>

          {showReview ? (
            <View
              style={[
                styles.reviewCard,
                {
                  backgroundColor: theme.surfaceElevated,
                  borderColor: theme.border,
                },
              ]}
            >
              <ThemedText
                style={[
                  styles.reviewTitle,
                  { color: theme.textPrimary },
                ]}
              >
                How was this story?
              </ThemedText>

              <ThemedText
                style={[
                  styles.reviewSubtitle,
                  { color: theme.textSecondary },
                ]}
              >
                Tell us what you and your child thought.
              </ThemedText>

              <ThemedText
                style={[
                  styles.questionLabel,
                  { color: theme.textPrimary },
                ]}
              >
                Rate this story from 1 to 10
              </ThemedText>

              <View style={styles.ratingRow}>
                {Array.from({ length: 10 }, (_, i) => i + 1).map((value) => (
                  <Pressable
                    key={value}
                    onPress={() => {
                      setRating(value);
                      setReviewSaved(false);
                    }}
                    style={[
                      styles.ratingButton,
                      {
                        backgroundColor:
                          rating === value
                            ? theme.accent
                            : theme.backgroundElement,
                        borderColor:
                          rating === value
                            ? theme.accent
                            : theme.border,
                      },
                    ]}
                  >
                    <ThemedText
                      style={{
                        color:
                          rating === value
                            ? theme.accentText
                            : theme.textPrimary,
                        fontWeight: '800',
                      }}
                    >
                      {value}
                    </ThemedText>
                  </Pressable>
                ))}
              </View>

              <ThemedText
                style={[
                  styles.questionLabel,
                  { color: theme.textPrimary },
                ]}
              >
                Did you like the story?
              </ThemedText>

              <View style={styles.optionRow}>
                <Pressable
                  onPress={() => {
                    setParentLiked(true);
                    setReviewSaved(false);
                  }}
                  style={[
                    styles.optionButton,
                    {
                      backgroundColor:
                        parentLiked === true
                          ? theme.accent
                          : theme.backgroundElement,
                      borderColor:
                        parentLiked === true
                          ? theme.accent
                          : theme.border,
                    },
                  ]}
                >
                  <ThemedText
                    style={{
                      color:
                        parentLiked === true
                          ? theme.accentText
                          : theme.textPrimary,
                      fontWeight: '700',
                    }}
                  >
                    Yes
                  </ThemedText>
                </Pressable>

                <Pressable
                  onPress={() => {
                    setParentLiked(false);
                    setReviewSaved(false);
                  }}
                  style={[
                    styles.optionButton,
                    {
                      backgroundColor:
                        parentLiked === false
                          ? theme.accent
                          : theme.backgroundElement,
                      borderColor:
                        parentLiked === false
                          ? theme.accent
                          : theme.border,
                    },
                  ]}
                >
                  <ThemedText
                    style={{
                      color:
                        parentLiked === false
                          ? theme.accentText
                          : theme.textPrimary,
                      fontWeight: '700',
                    }}
                  >
                    Not really
                  </ThemedText>
                </Pressable>
              </View>

              <ThemedText
                style={[
                  styles.questionLabel,
                  { color: theme.textPrimary },
                ]}
              >
                Did your child enjoy the story?
              </ThemedText>

              <View style={styles.optionRow}>
                {[
                  { label: 'Yes', value: 'yes' as const },
                  { label: 'A little', value: 'a_little' as const },
                  { label: 'No', value: 'no' as const },
                ].map((option) => (
                  <Pressable
                    key={option.value}
                    onPress={() => {
                      setChildSatisfied(option.value);
                      setReviewSaved(false);
                    }}
                    style={[
                      styles.optionButton,
                      {
                        backgroundColor:
                          childSatisfied === option.value
                            ? theme.accent
                            : theme.backgroundElement,
                        borderColor:
                          childSatisfied === option.value
                            ? theme.accent
                            : theme.border,
                      },
                    ]}
                  >
                    <ThemedText
                      style={{
                        color:
                          childSatisfied === option.value
                            ? theme.accentText
                            : theme.textPrimary,
                        fontWeight: '700',
                      }}
                    >
                      {option.label}
                    </ThemedText>
                  </Pressable>
                ))}
              </View>

              <ThemedText
                style={[
                  styles.questionLabel,
                  { color: theme.textPrimary },
                ]}
              >
                Was the story length right?
              </ThemedText>

              <View style={styles.optionRow}>
                {[
                  { label: 'Too short', value: 'too_short' as const },
                  { label: 'Just right', value: 'just_right' as const },
                  { label: 'Too long', value: 'too_long' as const },
                ].map((option) => (
                  <Pressable
                    key={option.value}
                    onPress={() => {
                      setLengthFeedback(option.value);
                      setReviewSaved(false);
                    }}
                    style={[
                      styles.optionButton,
                      {
                        backgroundColor:
                          lengthFeedback === option.value
                            ? theme.accent
                            : theme.backgroundElement,
                        borderColor:
                          lengthFeedback === option.value
                            ? theme.accent
                            : theme.border,
                      },
                    ]}
                  >
                    <ThemedText
                      style={{
                        color:
                          lengthFeedback === option.value
                            ? theme.accentText
                            : theme.textPrimary,
                        fontWeight: '700',
                      }}
                    >
                      {option.label}
                    </ThemedText>
                  </Pressable>
                ))}
              </View>

              <ThemedText
                style={[
                  styles.questionLabel,
                  { color: theme.textPrimary },
                ]}
              >
                How was the reading difficulty?
              </ThemedText>

              <View style={styles.optionRow}>
                {[
                  { label: 'Too easy', value: 'too_easy' as const },
                  { label: 'Just right', value: 'just_right' as const },
                  { label: 'Too difficult', value: 'too_difficult' as const },
                ].map((option) => (
                  <Pressable
                    key={option.value}
                    onPress={() => {
                      setDifficultyFeedback(option.value);
                      setReviewSaved(false);
                    }}
                    style={[
                      styles.optionButton,
                      {
                        backgroundColor:
                          difficultyFeedback === option.value
                            ? theme.accent
                            : theme.backgroundElement,
                        borderColor:
                          difficultyFeedback === option.value
                            ? theme.accent
                            : theme.border,
                      },
                    ]}
                  >
                    <ThemedText
                      style={{
                        color:
                          difficultyFeedback === option.value
                            ? theme.accentText
                            : theme.textPrimary,
                        fontWeight: '700',
                      }}
                    >
                      {option.label}
                    </ThemedText>
                  </Pressable>
                ))}
              </View>

              <ThemedText
                style={[
                  styles.questionLabel,
                  { color: theme.textPrimary },
                ]}
              >
                What would make the next story better?
              </ThemedText>

              <View style={styles.tagsRow}>
                {improvementOptions.map((tag) => {
                  const selected = improvementTags.includes(tag);

                  return (
                    <Pressable
                      key={tag}
                      onPress={() => toggleImprovementTag(tag)}
                      style={[
                        styles.tagButton,
                        {
                          backgroundColor:
                            selected
                              ? theme.accent
                              : theme.backgroundElement,
                          borderColor:
                            selected
                              ? theme.accent
                              : theme.border,
                        },
                      ]}
                    >
                      <ThemedText
                        style={{
                          color:
                            selected
                              ? theme.accentText
                              : theme.textPrimary,
                          fontWeight: '700',
                        }}
                      >
                        {tag}
                      </ThemedText>
                    </Pressable>
                  );
                })}
              </View>

              <ThemedText
                style={[
                  styles.questionLabel,
                  { color: theme.textPrimary },
                ]}
              >
                Anything else?
              </ThemedText>

              <TextInput
                value={comment}
                onChangeText={(value) => {
                  setComment(value);
                  setReviewSaved(false);
                }}
                placeholder="Optional comment..."
                placeholderTextColor={theme.textSecondary}
                multiline
                style={[
                  styles.commentInput,
                  {
                    color: theme.textPrimary,
                    backgroundColor: theme.backgroundElement,
                    borderColor: theme.border,
                  },
                ]}
              />

              {reviewError ? (
                <ThemedText style={styles.reviewError}>
                  {reviewError}
                </ThemedText>
              ) : null}

              {reviewSaved ? (
                <ThemedText
                  style={[
                    styles.reviewSuccess,
                    { color: theme.accent },
                  ]}
                >
                  Review saved ✓
                </ThemedText>
              ) : null}

              <Pressable
                onPress={handleSaveReview}
                style={[
                  styles.saveReviewButton,
                  { backgroundColor: theme.accent },
                ]}
              >
                <ThemedText
                  style={{
                    color: theme.accentText,
                    fontSize: 16,
                    fontWeight: '800',
                  }}
                >
                  Save Review
                </ThemedText>
              </Pressable>
            </View>
          ) : null}
        </ScrollView>
      </ThemedView>
    );
  }

  return (
    <ThemedView style={styles.container}>
      <ScrollView contentContainerStyle={[styles.pageContent, { paddingBottom: bottomPadding }]} showsVerticalScrollIndicator={false}>
        <ThemedText style={[styles.kicker, { color: theme.accent }]}>YOUR LIBRARY</ThemedText>
        <ThemedText style={[styles.title, { color: theme.textPrimary }]}>Saved Stories</ThemedText>
        <ThemedText themeColor="textSecondary" style={styles.subtitle}>All stories are kept safely on your device.</ThemedText>
        {stories.length > 0 ? (
          <View style={styles.filterRow}>
            <Pressable
              onPress={() => setShowFavorites(false)}
              style={[styles.filterButton, { backgroundColor: !showFavorites ? theme.accent : theme.surfaceElevated, borderColor: theme.border, borderWidth: 1 }]}>
              <ThemedText style={{ color: !showFavorites ? theme.accentText : theme.textSecondary, fontWeight: '700' }}>All</ThemedText>
            </Pressable>
            <Pressable
              onPress={() => setShowFavorites(true)}
              style={[styles.filterButton, { backgroundColor: showFavorites ? theme.accent : theme.surfaceElevated, borderColor: theme.border, borderWidth: 1 }]}>
              <ThemedText style={{ color: showFavorites ? theme.accentText : theme.textSecondary, fontWeight: '700' }}>♥ Favorites</ThemedText>
            </Pressable>
          </View>
        ) : null}
        {loading ? <ThemedText>Opening library...</ThemedText> : stories.length === 0 ? (
          <View style={styles.emptyState}>
            <ThemedText style={[styles.emptyEmoji, { color: theme.accent }]}>✦</ThemedText>
            <ThemedText style={styles.emptyTitle}>Your bookshelf is empty</ThemedText>
            <ThemedText themeColor="textSecondary">Your first adventure is waiting.</ThemedText>
            <Pressable onPress={() => router.navigate('/')} style={[styles.readerAction, { backgroundColor: theme.accent }]}>
              <ThemedText style={{ color: theme.accentText, fontWeight: '800', fontSize: 16 }}>✨ Create your first story</ThemedText>
            </Pressable>
          </View>
        ) : filteredStories.length === 0 ? (
          <View style={styles.emptyState}><ThemedText style={[styles.emptyEmoji, { color: theme.accent }]}>♡</ThemedText><ThemedText style={styles.emptyTitle}>No favorites yet ♥</ThemedText></View>
        ) : (
          <View style={styles.booksGrid}>
            {filteredStories.map((story) => (
              <Pressable key={story.id} onPress={() => setActiveStory(story)} style={[styles.bookCard, { backgroundColor: theme.surfaceElevated, borderColor: theme.border, borderWidth: 1 }]}>
                <View style={[styles.bookCover, { backgroundColor: theme.backgroundElement, borderColor: theme.border, borderWidth: 1 }]}><ThemedText style={styles.bookEmoji}>{story.emoji}</ThemedText><ThemedText style={[styles.coverLabel, { color: theme.accent }]}>STORY</ThemedText></View>
                <View style={styles.cardRow}><ThemedText style={[styles.bookTitle, { color: theme.textPrimary }]} numberOfLines={2}>{story.title}</ThemedText><Pressable onPress={() => handleToggleFavorite(story.id)}><ThemedText style={[styles.favoriteText, { color: story.isFavorite ? '#FF4D6D' : theme.textSecondary }]}>{story.isFavorite ? '♥' : '♡'}</ThemedText></Pressable></View>
                <ThemedText type="small" themeColor="textSecondary">{story.character} • Ages {story.age} • ⏱ {getReadingDuration(story.story, story.age)}</ThemedText>
                <ThemedText type="small" themeColor="textSecondary">{new Date(story.createdAt).toLocaleDateString()}</ThemedText>
              </Pressable>
            ))}
          </View>
        )}
        {stories.length > 0 ? <Pressable onPress={confirmClear} style={styles.clearButton}><ThemedText themeColor="textSecondary">Wipe local bookshelf</ThemedText></Pressable> : null}
      </ScrollView>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  pageContent: { width: '100%', maxWidth: 440, alignSelf: 'center', padding: 20, gap: 10 },
  readerContent: { width: '100%', maxWidth: 440, alignSelf: 'center', padding: 20, alignItems: 'center' },
  kicker: { fontSize: 11, fontWeight: '800', letterSpacing: 1.5 },
  title: { fontSize: 32, lineHeight: 38, fontWeight: '800' },
  subtitle: { fontSize: 15, lineHeight: 22, marginBottom: 14 },
  filterRow: { flexDirection: 'row', gap: 8, marginBottom: 10 },
  filterButton: { minHeight: 40, paddingHorizontal: 16, borderRadius: 16, justifyContent: 'center' },
  booksGrid: { gap: 14 },
  bookCard: { borderRadius: 22, padding: 14, gap: 6 },
  bookCover: { height: 150, borderRadius: 18, alignItems: 'center', justifyContent: 'center', position: 'relative' },
  bookEmoji: { fontSize: 58 },
  coverLabel: { position: 'absolute', bottom: 12, fontSize: 9, fontWeight: '800', letterSpacing: 1.2 },
  cardRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8 },
  bookTitle: { flex: 1, fontSize: 18, lineHeight: 22, fontWeight: '800' },
  favoriteText: { fontSize: 24, fontWeight: '700' },
  emptyState: { alignItems: 'center', paddingVertical: 80, gap: 8 },
  emptyEmoji: { fontSize: 42 },
  emptyTitle: { fontSize: 20, fontWeight: '800' },
  readerToolbar: { width: '100%', flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  toolbarActions: { flexDirection: 'row', gap: 8 },
  toolButton: { minHeight: 42, paddingHorizontal: 14, borderRadius: 14, justifyContent: 'center' },
  readerCover: { width: '100%', height: 230, borderRadius: 26, alignItems: 'center', justifyContent: 'center', marginBottom: 20 },
  readerEmoji: { fontSize: 78 },
  readerTitle: { fontSize: 32, lineHeight: 38, fontWeight: '800', textAlign: 'center' },
  readerMeta: { fontSize: 14, textAlign: 'center', marginTop: 6 },
  divider: { width: 48, height: 2, marginVertical: 24 },
  readerStory: { width: '100%', fontSize: 19, lineHeight: 31 },
  readerAction: { width: '100%', minHeight: 54, borderRadius: 18, paddingHorizontal: 22, justifyContent: 'center', alignItems: 'center', marginTop: 28, marginBottom: 12 },
  clearButton: { alignItems: 'center', paddingVertical: 20 },

  reviewToggle: {
    width: '100%',
    minHeight: 50,
    borderRadius: 18,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 4,
  },

  reviewCard: {
    width: '100%',
    borderRadius: 24,
    borderWidth: 1,
    padding: 18,
    marginTop: 14,
    gap: 12,
  },

  reviewTitle: {
    fontSize: 24,
    lineHeight: 30,
    fontWeight: '800',
  },

  reviewSubtitle: {
    fontSize: 14,
    lineHeight: 21,
    marginBottom: 4,
  },

  questionLabel: {
    fontSize: 15,
    lineHeight: 20,
    fontWeight: '800',
    marginTop: 8,
  },

  ratingRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 7,
  },

  ratingButton: {
    width: 38,
    height: 38,
    borderRadius: 12,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },

  optionRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },

  optionButton: {
    minHeight: 42,
    borderRadius: 14,
    borderWidth: 1,
    paddingHorizontal: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },

  tagsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },

  tagButton: {
    minHeight: 40,
    borderRadius: 16,
    borderWidth: 1,
    paddingHorizontal: 13,
    alignItems: 'center',
    justifyContent: 'center',
  },

  commentInput: {
    minHeight: 96,
    borderRadius: 16,
    borderWidth: 1,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 15,
    lineHeight: 21,
    textAlignVertical: 'top',
  },

  saveReviewButton: {
    minHeight: 52,
    borderRadius: 17,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 6,
  },

  reviewSuccess: {
    fontWeight: '800',
    fontSize: 14,
  },

  reviewError: {
    color: '#D64545',
    fontWeight: '700',
    fontSize: 14,
  },
});
