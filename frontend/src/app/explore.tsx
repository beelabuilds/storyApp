import { useEffect, useState } from 'react';
import { Alert, Platform, Pressable, ScrollView, StyleSheet, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { BottomTabInset, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';
import { Story, useLocalStories } from '@/hooks/use-local-stories';

export default function ExploreScreen() {
  const theme = useTheme();
  const router = useRouter();
  const safeAreaInsets = useSafeAreaInsets();
  const { storyId } = useLocalSearchParams<{ storyId?: string }>();
  const { stories, loading, deleteStory, clearAllStories, refreshStories, toggleFavorite } = useLocalStories();
  const [activeStory, setActiveStory] = useState<Story | null>(null);
  const [showFavorites, setShowFavorites] = useState(false);

  useEffect(() => { refreshStories(); }, []);
  useEffect(() => {
    if (storyId) setActiveStory(stories.find((story) => story.id === storyId) ?? null);
  }, [stories, storyId]);

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
  const bottomPadding = safeAreaInsets.bottom + BottomTabInset + 32;
  const handleToggleFavorite = async (id: string) => {
    const updatedStory = await toggleFavorite(id);
    if (updatedStory && activeStory?.id === id) setActiveStory(updatedStory);
  };

  if (activeStory) {
    return (
      <ThemedView style={styles.container}>
        <ScrollView contentContainerStyle={[styles.readerContent, { paddingBottom: bottomPadding }]} showsVerticalScrollIndicator={false}>
          <View style={styles.readerToolbar}>
            <Pressable onPress={() => { setActiveStory(null); router.navigate('/explore'); }} style={styles.toolButton}>
              <ThemedText>← Back to Stories</ThemedText>
            </Pressable>
            <View style={styles.toolbarActions}>
              <Pressable onPress={() => handleToggleFavorite(activeStory.id)} style={styles.toolButton}>
                <ThemedText style={styles.favoriteText}>{activeStory.isFavorite ? '♥' : '♡'}</ThemedText>
              </Pressable>
              <Pressable onPress={() => confirmDelete(activeStory.id, activeStory.title)} style={styles.toolButton}>
                <ThemedText>•••</ThemedText>
              </Pressable>
            </View>
          </View>
          <View style={styles.readerCover}>
            <ThemedText style={styles.readerEmoji}>{activeStory.emoji}</ThemedText>
            <ThemedText style={styles.coverLabel}>YOUR STORY</ThemedText>
          </View>
          <ThemedText style={styles.readerTitle}>{activeStory.title}</ThemedText>
          <ThemedText themeColor="textSecondary" style={styles.readerMeta}>Ages {activeStory.age} • {activeStory.character}</ThemedText>
          <View style={styles.divider} />
          <ThemedText style={styles.readerStory}>{activeStory.story}</ThemedText>
          <Pressable onPress={() => handleToggleFavorite(activeStory.id)} style={[styles.readerAction, { backgroundColor: theme.accent }]}>
            <ThemedText themeColor="accentText">{activeStory.isFavorite ? '♥ Favorited' : '♡ Add to Favorites'}</ThemedText>
          </Pressable>
        </ScrollView>
      </ThemedView>
    );
  }

  return (
    <ThemedView style={styles.container}>
      <ScrollView contentContainerStyle={[styles.pageContent, { paddingBottom: bottomPadding }]} showsVerticalScrollIndicator={false}>
        <ThemedText style={styles.kicker}>YOUR LIBRARY</ThemedText>
        <ThemedText style={styles.title}>Saved Stories</ThemedText>
        <ThemedText themeColor="textSecondary" style={styles.subtitle}>All stories are kept safely on your device.</ThemedText>
        {stories.length > 0 ? (
          <View style={styles.filterRow}>
            <Pressable onPress={() => setShowFavorites(false)} style={[styles.filterButton, !showFavorites && { backgroundColor: theme.accent }]}>
              <ThemedText themeColor={!showFavorites ? 'accentText' : 'textSecondary'}>All</ThemedText>
            </Pressable>
            <Pressable onPress={() => setShowFavorites(true)} style={[styles.filterButton, showFavorites && { backgroundColor: theme.accent }]}>
              <ThemedText themeColor={showFavorites ? 'accentText' : 'textSecondary'}>♥ Favorites</ThemedText>
            </Pressable>
          </View>
        ) : null}
        {loading ? <ThemedText>Opening library...</ThemedText> : stories.length === 0 ? (
          <View style={styles.emptyState}>
            <ThemedText style={styles.emptyEmoji}>✦</ThemedText>
            <ThemedText style={styles.emptyTitle}>Your bookshelf is empty</ThemedText>
            <ThemedText themeColor="textSecondary">Your first adventure is waiting.</ThemedText>
            <Pressable onPress={() => router.navigate('/create')} style={[styles.readerAction, { backgroundColor: theme.accent }]}>
              <ThemedText themeColor="accentText">✨ Create your first story</ThemedText>
            </Pressable>
          </View>
        ) : filteredStories.length === 0 ? (
          <View style={styles.emptyState}><ThemedText style={styles.emptyEmoji}>♡</ThemedText><ThemedText style={styles.emptyTitle}>No favorites yet ♥</ThemedText></View>
        ) : (
          <View style={styles.booksGrid}>
            {filteredStories.map((story) => (
              <Pressable key={story.id} onPress={() => setActiveStory(story)} style={[styles.bookCard, { backgroundColor: theme.backgroundElement }]}>
                <View style={styles.bookCover}><ThemedText style={styles.bookEmoji}>{story.emoji}</ThemedText><ThemedText style={styles.coverLabel}>STORY</ThemedText></View>
                <View style={styles.cardRow}><ThemedText style={styles.bookTitle} numberOfLines={2}>{story.title}</ThemedText><Pressable onPress={() => handleToggleFavorite(story.id)}><ThemedText style={styles.favoriteText}>{story.isFavorite ? '♥' : '♡'}</ThemedText></Pressable></View>
                <ThemedText type="small" themeColor="textSecondary">{story.character} • Ages {story.age}</ThemedText>
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
  kicker: { color: '#F7D77A', fontSize: 11, fontWeight: '800', letterSpacing: 1.5 },
  title: { fontSize: 32, lineHeight: 38, fontWeight: '800' },
  subtitle: { fontSize: 15, lineHeight: 22, marginBottom: 14 },
  filterRow: { flexDirection: 'row', gap: 8, marginBottom: 10 },
  filterButton: { minHeight: 40, paddingHorizontal: 16, borderRadius: 16, justifyContent: 'center' },
  booksGrid: { gap: 14 },
  bookCard: { borderRadius: 22, padding: 14, gap: 6 },
  bookCover: { height: 150, borderRadius: 18, backgroundColor: '#40365E', alignItems: 'center', justifyContent: 'center', position: 'relative' },
  bookEmoji: { fontSize: 58 },
  coverLabel: { position: 'absolute', bottom: 12, color: '#F7D77A', fontSize: 9, fontWeight: '800', letterSpacing: 1.2 },
  cardRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8 },
  bookTitle: { flex: 1, fontSize: 18, lineHeight: 22, fontWeight: '800' },
  favoriteText: { color: '#F7D77A', fontSize: 24 },
  emptyState: { alignItems: 'center', paddingVertical: 80, gap: 8 },
  emptyEmoji: { color: '#F7D77A', fontSize: 42 },
  emptyTitle: { fontSize: 20, fontWeight: '800' },
  readerToolbar: { width: '100%', flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  toolbarActions: { flexDirection: 'row', gap: 8 },
  toolButton: { minHeight: 42, paddingHorizontal: 12, borderRadius: 14, backgroundColor: '#25213D', justifyContent: 'center' },
  readerCover: { width: '100%', height: 230, borderRadius: 26, backgroundColor: '#40365E', alignItems: 'center', justifyContent: 'center', marginBottom: 20 },
  readerEmoji: { fontSize: 78 },
  readerTitle: { fontSize: 32, lineHeight: 38, fontWeight: '800', textAlign: 'center' },
  readerMeta: { fontSize: 14, textAlign: 'center', marginTop: 6 },
  divider: { width: 48, height: 2, backgroundColor: '#F7D77A', marginVertical: 24 },
  readerStory: { width: '100%', fontSize: 19, lineHeight: 31 },
  readerAction: { minHeight: 54, borderRadius: 18, paddingHorizontal: 22, justifyContent: 'center', alignItems: 'center', marginTop: 28 },
  clearButton: { alignItems: 'center', paddingVertical: 20 },
});
