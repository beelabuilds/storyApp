import { useEffect, useRef, useState } from 'react';
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, TextInput, View } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { SymbolView } from 'expo-symbols';
import Constants from 'expo-constants';

import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { useLocalStories, Story } from '@/hooks/use-local-stories';
import { useTheme, useThemeMode } from '@/hooks/use-theme';

export const getApiUrl = () => {
  if (Platform.OS === 'web') return 'http://localhost:8000';
  const hostUri = Constants.expoConfig?.hostUri;
  if (hostUri) {
    const ip = hostUri.split(':')[0];
    return `http://${ip}:8000`;
  }
  return Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://localhost:8000';
};

export const getReadingDuration = (text: string, age?: string): string => {
  if (!text) return '3–5 min read';
  const words = text.trim().split(/\s+/).filter(Boolean).length;
  const ageStr = String(age || '').trim().toLowerCase();

  // Explicit age table matching
  if (ageStr) {
    if (ageStr.includes('8') && !ageStr.includes('6-8') && !ageStr.includes('6–8') && !ageStr.includes('4-8') && !ageStr.includes('4–8')) {
      return '7–10 min read';
    }
    if (ageStr.includes('7') && !ageStr.includes('6-8') && !ageStr.includes('6–8')) {
      return '6–8 min read';
    }
    if (ageStr.includes('6-8') || ageStr.includes('6–8') || ageStr.includes('6')) {
      if (words >= 600) return '6–8 min read';
      return '5–7 min read';
    }
    if (ageStr.includes('5')) {
      return '4–6 min read';
    }
    if (ageStr.includes('4-5') || ageStr.includes('4–5') || ageStr.includes('4')) {
      return '3–5 min read';
    }
  }

  // Word count based reading duration
  if (words >= 650) return '7–10 min read';
  if (words >= 550) return '6–8 min read';
  if (words >= 450) return '5–7 min read';
  if (words >= 350) return '4–6 min read';
  return '3–5 min read';
};

const suggestions = ['Bedtime story', 'Something happened today', 'Help with a fear', 'Build confidence', 'Teach kindness', 'Just for fun'];
const ageSuggestions = ['4–5 years', '6–8 years', '4–8 years'];
const heroSuggestions = ['My child', 'Friendly puppy', 'Magical dragon', 'Curious astronaut'];

type Message = {
  id: string;
  role: 'assistant' | 'user';
  text: string;
  chips?: string[];
  story?: Story;
};
type StoryContext = { age?: string; dailyEvent?: string; hero?: string; goal?: string; [key: string]: unknown };

const initialContext: StoryContext = { age: '', dailyEvent: '', hero: '', goal: '' };

export default function HomeChat() {
  const theme = useTheme();
  const { mode, toggleMode } = useThemeMode();
  const router = useRouter();
  const { stories, saveStory, toggleFavorite } = useLocalStories();
  const [messages, setMessages] = useState<Message[]>([]);
  const [context, setContext] = useState<StoryContext>(initialContext);
  const [input, setInput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const scrollRef = useRef<ScrollView>(null);

  useEffect(() => {
    if (!messages.length) {
      setMessages([{
        id: 'welcome',
        role: 'assistant',
        text: "Hi! What kind of story would you like to create for your child today?",
        chips: suggestions.slice(0, 4)
      }]);
    }
  }, [messages.length]);

  const addMessage = (message: Omit<Message, 'id'>) => setMessages((previous) => [...previous, { ...message, id: `${Date.now()}-${previous.length}` }]);

  const sendToAssistant = async (conversation: Message[]) => {
    setIsGenerating(true);
    try {
      const baseUrl = getApiUrl();
      const response = await fetch(`${baseUrl}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: conversation.map(({ role, text }) => ({ role, content: text })),
          storyContext: context,
        }),
      });
      if (!response.ok) throw new Error(`Server returned ${response.status}`);
      const data = await response.json();
      const nextContext = { ...context, ...(data.storyContext || {}) };
      setContext(nextContext);

      let attachedStory: Story | undefined = undefined;
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
            event: String(nextContext.dailyEvent || ''),
            goal: String(nextContext.goal || 'Just for fun'),
            character: String(nextContext.hero || 'A friendly explorer'),
            age: String(nextContext.age || '6-8'),
            createdAt: new Date().toISOString(),
            emoji: '✦',
            isFavorite: false,
            readingProgress: 0
          };
        }
      }

      addMessage({
        role: 'assistant',
        text: data.assistantMessage || 'I am here to help.',
        chips: data.suggestions,
        story: attachedStory,
      });
    } catch (err) {
      console.error('API Error:', err);
      addMessage({
        role: 'assistant',
        text: 'I could not reach the story engine. Please check that the local story server is running.'
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleChipPress = (chip: string) => {
    const currentTyped = input.trim();
    if (currentTyped) {
      // Combine selected chip + parent's typed answer
      const combined = `${chip}: ${currentTyped}`;
      void submit(combined);
    } else {
      // Send selected suggestion
      void submit(chip);
    }
  };

  const submit = async (rawText: string) => {
    const text = rawText.trim();
    if (!text || isGenerating) return;
    setInput('');
    const nextMessages = [...messages, { id: `${Date.now()}-${messages.length}`, role: 'user' as const, text }];
    setMessages(nextMessages);
    await sendToAssistant(nextMessages);
  };

  const handleReadStory = async (story: Story) => {
    const saved = await saveStory(story);
    router.push({ pathname: '/explore', params: { storyId: saved.id } });
  };

  const handleToggleStoryBookmark = async (story: Story, messageId: string) => {
    const updatedFavorite = !story.isFavorite;
    await saveStory({ ...story, isFavorite: updatedFavorite });
    setMessages((prev) =>
      prev.map((msg) =>
        msg.id === messageId && msg.story
          ? { ...msg, story: { ...msg.story, isFavorite: updatedFavorite } }
          : msg
      )
    );
  };

  const startNewChat = () => {
    setMessages([]);
    setContext(initialContext);
  };

  return (
    <ThemedView style={styles.container}>
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.header}>
          <View>
            <ThemedText style={styles.headerTitle}>Story Assistant</ThemedText>
            <ThemedText type="small" themeColor="textSecondary">Personalized stories for little readers</ThemedText>
          </View>
          <View style={styles.headerActions}>
            <Pressable
              onPress={toggleMode}
              accessibilityLabel="Toggle theme"
              style={[styles.iconButton, { backgroundColor: theme.surfaceElevated, borderColor: theme.border, borderWidth: 1 }]}>
              <ThemedText style={[styles.headerIconText, { color: theme.textPrimary }]}>
                {mode === 'dark' ? '☀' : '☾'}
              </ThemedText>
            </Pressable>
            <Pressable
              onPress={startNewChat}
              accessibilityLabel="Start new story chat"
              style={[styles.iconButton, { backgroundColor: theme.surfaceElevated, borderColor: theme.border, borderWidth: 1 }]}>
              <ThemedText style={[styles.headerIconText, { color: theme.textPrimary }]}>
                +
              </ThemedText>
            </Pressable>
          </View>
        </View>

        <KeyboardAvoidingView style={styles.chatArea} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
          <ScrollView
            ref={scrollRef}
            style={styles.messages}
            contentContainerStyle={styles.messagesContent}
            keyboardShouldPersistTaps="handled"
            onContentSizeChange={() => scrollRef.current?.scrollToEnd({ animated: true })}>
            
            {messages.length <= 1 ? (
              <View style={styles.emptyWelcome}>
                <ThemedText style={styles.welcomeTitle}>Create a story together ✨</ThemedText>
                <ThemedText themeColor="textSecondary" style={styles.welcomeText}>
                  Tell me about your child's day, imagination, or something you'd like them to learn.
                </ThemedText>
              </View>
            ) : null}

            {messages.map((message, index) => {
              const isLatestAssistantMessage = message.role === 'assistant' && index === messages.length - 1;
              return (
                <View key={message.id} style={[styles.messageBlock, message.role === 'user' && styles.userBlock]}>
                  <ThemedText
                    style={message.role === 'user'
                      ? [styles.userBubble, { backgroundColor: theme.accent, color: theme.accentText }]
                      : [styles.assistantText, { color: theme.textPrimary }]
                    }>
                    {message.text}
                  </ThemedText>

                  {message.story ? (
                    <View style={[styles.storyCard, { backgroundColor: theme.surfaceElevated, borderColor: theme.border, borderWidth: 1 }]}>
                      <ThemedText style={[styles.storyEyebrow, { color: theme.accent }]}>
                        A STORY FOR {String(message.story.character).toUpperCase()}
                      </ThemedText>
                      <ThemedText style={[styles.storyTitle, { color: theme.textPrimary }]}>{message.story.title}</ThemedText>
                      <ThemedText type="small" themeColor="textSecondary">
                        For ages {message.story.age} • ⏱ {getReadingDuration(message.story.story, message.story.age)}
                      </ThemedText>
                      <ThemedText style={[styles.storyPreview, { color: theme.textPrimary }]} numberOfLines={6}>
                        {message.story.story}
                      </ThemedText>
                      <View style={styles.storyActions}>
                        <Pressable onPress={() => handleReadStory(message.story!)} style={[styles.readButton, { backgroundColor: theme.accent }]}>
                          <ThemedText style={{ color: theme.accentText, fontWeight: '800', fontSize: 16 }}>
                            Read full story
                          </ThemedText>
                        </Pressable>
                        <Pressable
                          onPress={() => handleToggleStoryBookmark(message.story!, message.id)}
                          style={[styles.bookmarkButton, { backgroundColor: theme.backgroundElement, borderColor: theme.border, borderWidth: 1 }]}>
                          <ThemedText style={[styles.bookmarkIcon, { color: message.story.isFavorite ? '#FF4D6D' : theme.textPrimary }]}>
                            {message.story.isFavorite ? '♥' : '♡'}
                          </ThemedText>
                        </Pressable>
                      </View>
                    </View>
                  ) : null}

                  {isLatestAssistantMessage && message.chips && message.chips.length > 0 && !isGenerating ? (
                    <View style={styles.chips}>
                      {message.chips.map((chip) => (
                        <Pressable
                          key={chip}
                          onPress={() => handleChipPress(chip)}
                          style={[styles.chip, { backgroundColor: theme.surfaceElevated, borderColor: theme.border, borderWidth: 1 }]}>
                          <ThemedText type="small" style={[styles.chipText, { color: theme.textPrimary }]}>
                            {chip}
                          </ThemedText>
                        </Pressable>
                      ))}
                    </View>
                  ) : null}
                </View>
              );
            })}

            {isGenerating ? (
              <ThemedText themeColor="textSecondary" style={styles.thinking}>
                ✨ Writing something wonderful...
              </ThemedText>
            ) : null}
          </ScrollView>

          <View style={[styles.composer, { backgroundColor: theme.surfaceElevated, borderColor: theme.border, borderWidth: 1 }]}>
            <TextInput
              value={input}
              onChangeText={setInput}
              onSubmitEditing={() => submit(input)}
              onKeyPress={(event) => {
                const keyEvent = event.nativeEvent as typeof event.nativeEvent & { key?: string; shiftKey?: boolean };
                if (Platform.OS === 'web' && keyEvent.key === 'Enter' && !keyEvent.shiftKey) {
                  void submit(input);
                }
              }}
              multiline
              placeholder="Type your answer or request a story..."
              placeholderTextColor={theme.textSecondary}
              style={[styles.input, { color: theme.textPrimary }]}
            />
            <Pressable
              onPress={() => submit(input)}
              accessibilityLabel="Send message"
              style={[styles.sendButton, { backgroundColor: theme.accent }]}>
              <ThemedText style={{ color: theme.accentText, fontSize: 18, fontWeight: '900' }}>
                ↑
              </ThemedText>
            </Pressable>
          </View>
        </KeyboardAvoidingView>
      </SafeAreaView>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  safeArea: { flex: 1, maxWidth: 520, width: '100%', alignSelf: 'center', paddingHorizontal: 20, paddingBottom: 88 },
  header: { minHeight: 64, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  headerTitle: { fontSize: 20, fontWeight: '800' },
  headerActions: { flexDirection: 'row', gap: 8 },
  iconButton: { width: 42, height: 42, borderRadius: 21, alignItems: 'center', justifyContent: 'center' },
  headerIconText: { fontSize: 18, fontWeight: '700' },
  chatArea: { flex: 1 },
  messages: { flex: 1 },
  messagesContent: { paddingTop: 18, paddingBottom: 18, gap: 20 },
  emptyWelcome: { alignItems: 'center', paddingVertical: 60, paddingHorizontal: 20 },
  welcomeTitle: { fontSize: 28, lineHeight: 34, fontWeight: '800', textAlign: 'center' },
  welcomeText: { textAlign: 'center', fontSize: 15, lineHeight: 22, marginTop: 10 },
  messageBlock: { alignSelf: 'flex-start', maxWidth: '92%', gap: 10 },
  userBlock: { alignSelf: 'flex-end', alignItems: 'flex-end' },
  assistantText: { fontSize: 16, lineHeight: 24, fontWeight: '500' },
  userBubble: { paddingHorizontal: 16, paddingVertical: 10, borderRadius: 20, fontSize: 16, lineHeight: 22, fontWeight: '600' },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 4 },
  chip: { borderRadius: 18, paddingHorizontal: 14, paddingVertical: 9 },
  chipText: { fontSize: 14, fontWeight: '600' },
  storyCard: { borderRadius: 22, padding: 20, gap: 10, marginTop: 8 },
  storyEyebrow: { fontSize: 11, fontWeight: '800', letterSpacing: 1.2 },
  storyTitle: { fontSize: 26, lineHeight: 32, fontWeight: '800' },
  storyPreview: { fontSize: 16, lineHeight: 26, marginTop: 6 },
  storyActions: { flexDirection: 'row', alignItems: 'center', gap: 10, marginTop: 12 },
  readButton: { flex: 1, minHeight: 48, borderRadius: 16, alignItems: 'center', justifyContent: 'center' },
  bookmarkButton: { width: 48, height: 48, borderRadius: 16, alignItems: 'center', justifyContent: 'center' },
  bookmarkIcon: { fontSize: 22, fontWeight: '700' },
  thinking: { fontSize: 14, fontStyle: 'italic', marginVertical: 4 },
  composer: { minHeight: 60, borderRadius: 22, marginBottom: 8, padding: 6, flexDirection: 'row', alignItems: 'flex-end', gap: 8 },
  input: { flex: 1, paddingHorizontal: 14, paddingVertical: 10, maxHeight: 110, fontSize: 16 },
  sendButton: { width: 44, height: 44, borderRadius: 16, alignItems: 'center', justifyContent: 'center' },
});
