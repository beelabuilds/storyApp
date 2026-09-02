import { useEffect, useRef, useState } from 'react';
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, TextInput, View } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { SymbolView } from 'expo-symbols';

import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { useLocalStories, Story } from '@/hooks/use-local-stories';
import { useTheme, useThemeMode } from '@/hooks/use-theme';

const suggestions = ['Bedtime story', 'Something happened today', 'Help with a fear', 'Build confidence', 'Teach kindness', 'Just for fun'];
const ageSuggestions = ['3–5 years', '6–8 years', '9–12 years'];
const heroSuggestions = ['My child', 'Friendly puppy', 'Magical dragon', 'Curious astronaut'];

type Message = { id: string; role: 'assistant' | 'user'; text: string; chips?: string[] };
type StoryContext = { age?: string; dailyEvent?: string; hero?: string; goal?: string; [key: string]: unknown };

const initialContext: StoryContext = { age: '', dailyEvent: '', hero: '', goal: '' };

export default function HomeChat() {
  const theme = useTheme();
  const { mode, toggleMode } = useThemeMode();
  const router = useRouter();
  const { stories, saveStory, toggleFavorite } = useLocalStories();
  const [messages, setMessages] = useState<Message[]>([]);
  const [context, setContext] = useState<StoryContext>(initialContext);
  const [currentStory, setCurrentStory] = useState<Story | null>(null);
  const [input, setInput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const scrollRef = useRef<ScrollView>(null);

  useEffect(() => {
    if (!messages.length) {
      setMessages([{ id: 'welcome', role: 'assistant', text: "Hi! What kind of story would you like to create for your child today?", chips: suggestions.slice(0, 4) }]);
    }
  }, [messages.length]);

  const addMessage = (message: Omit<Message, 'id'>) => setMessages((previous) => [...previous, { ...message, id: `${Date.now()}-${previous.length}` }]);

  const sendToAssistant = async (conversation: Message[]) => {
    setIsGenerating(true);
    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: conversation.map(({ role, text }) => ({ role, content: text })), storyContext: context, currentStory }),
      });
      if (!response.ok) throw new Error(`Server returned ${response.status}`);
      const data = await response.json();
      const nextContext = { ...context, ...(data.storyContext || {}) };
      setContext(nextContext);
      addMessage({ role: 'assistant', text: data.assistantMessage || 'I am here to help.', chips: data.suggestions });
      if (data.story) {
        setCurrentStory({ id: data.type === 'story' ? '' : currentStory?.id ?? '', title: data.story.title || 'A New Adventure', story: data.story.content || data.story.story || '', event: String(nextContext.dailyEvent || messages.find((message) => message.role === 'user')?.text || ''), goal: String(nextContext.goal || 'Just for fun'), character: String(nextContext.hero || 'A friendly explorer'), age: String(nextContext.age || '6-8'), createdAt: data.type === 'story' ? new Date().toISOString() : currentStory?.createdAt ?? new Date().toISOString(), emoji: '✦', isFavorite: data.type === 'story' ? false : currentStory?.isFavorite ?? false, readingProgress: 0 });
      }
    } catch {
      addMessage({ role: 'assistant', text: 'I could not reach the story engine. Please check that the local story server is running.' });
    } finally { setIsGenerating(false); }
  };

  const submit = async (rawText: string) => {
    const text = rawText.trim();
    if (!text || isGenerating) return;
    setInput('');
    const nextMessages = [...messages, { id: `${Date.now()}-${messages.length}`, role: 'user' as const, text }];
    setMessages(nextMessages);
    await sendToAssistant(nextMessages);
  };

  const saveCurrentStory = async () => {
    if (!currentStory) return;
    if (currentStory.id) {
      const updated = await toggleFavorite(currentStory.id);
      if (updated) setCurrentStory(updated);
      return;
    }
    const saved = await saveStory({ ...currentStory, isFavorite: true });
    setCurrentStory(saved);
    addMessage({ role: 'assistant', text: 'Saved to your bookmarks ✨' });
  };

  const readCurrentStory = async () => {
    if (!currentStory) return;
    const saved = currentStory.id ? currentStory : await saveStory(currentStory);
    setCurrentStory(saved);
    router.push({ pathname: '/explore', params: { storyId: saved.id } });
  };

  const startNewChat = () => { setMessages([]); setContext(initialContext); setCurrentStory(null); };

  return (
    <ThemedView style={styles.container}>
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.header}>
          <View><ThemedText style={styles.headerTitle}>Story Assistant</ThemedText><ThemedText type="small" themeColor="textSecondary">Personalized stories for little readers</ThemedText></View>
          <View style={styles.headerActions}>
            <Pressable onPress={toggleMode} style={[styles.iconButton, { backgroundColor: theme.backgroundElement }]}><SymbolView name={mode === 'dark' ? 'sun.max' : 'moon'} tintColor={theme.accent} size={19} /></Pressable>
            <Pressable onPress={startNewChat} style={[styles.iconButton, { backgroundColor: theme.backgroundElement }]}><SymbolView name="plus" tintColor={theme.text} size={20} /></Pressable>
          </View>
        </View>
        <KeyboardAvoidingView style={styles.chatArea} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
          <ScrollView ref={scrollRef} style={styles.messages} contentContainerStyle={styles.messagesContent} keyboardShouldPersistTaps="handled" onContentSizeChange={() => scrollRef.current?.scrollToEnd({ animated: true })}>
            {!currentStory && messages.length <= 1 ? <View style={styles.emptyWelcome}><ThemedText style={styles.welcomeTitle}>Create a story together ✨</ThemedText><ThemedText themeColor="textSecondary" style={styles.welcomeText}>Tell me about your child's day, imagination, or something you'd like them to learn.</ThemedText></View> : null}
            {messages.map((message) => <View key={message.id} style={[styles.messageBlock, message.role === 'user' && styles.userBlock]}><ThemedText themeColor={message.role === 'user' ? 'accentText' : undefined} style={message.role === 'user' ? styles.userBubble : styles.assistantText}>{message.text}</ThemedText>{message.chips ? <View style={styles.chips}>{message.chips.map((chip) => <Pressable key={chip} onPress={() => submit(chip)} style={[styles.chip, { backgroundColor: theme.backgroundElement }]}><ThemedText type="small" themeColor="textSecondary">{chip}</ThemedText></Pressable>)}</View> : null}</View>)}
            {currentStory ? <View style={[styles.storyCard, { backgroundColor: theme.backgroundElement }]}><ThemedText style={styles.storyEyebrow}>A STORY FOR {String(context.hero || currentStory.character).toUpperCase()}</ThemedText><ThemedText style={styles.storyTitle}>{currentStory.title}</ThemedText><ThemedText type="small" themeColor="textSecondary">For ages {context.age || currentStory.age}</ThemedText><ThemedText style={styles.storyPreview} numberOfLines={6}>{currentStory.story}</ThemedText><View style={styles.storyActions}><Pressable onPress={readCurrentStory} style={[styles.readButton, { backgroundColor: theme.accent }]}><ThemedText themeColor="accentText">Read full story</ThemedText></Pressable><Pressable onPress={saveCurrentStory} style={[styles.bookmarkButton, { backgroundColor: theme.backgroundSelected }]}><SymbolView name="bookmark" tintColor={currentStory.isFavorite ? theme.accent : theme.textSecondary} size={22} /></Pressable></View></View> : null}
            {isGenerating ? <ThemedText themeColor="textSecondary" style={styles.thinking}>Writing something wonderful...</ThemedText> : null}
          </ScrollView>
          <View style={[styles.composer, { backgroundColor: theme.backgroundElement }]}><TextInput value={input} onChangeText={setInput} onSubmitEditing={() => submit(input)} onKeyPress={(event) => { const keyEvent = event.nativeEvent as typeof event.nativeEvent & { key?: string; shiftKey?: boolean }; if (Platform.OS === 'web' && keyEvent.key === 'Enter' && !keyEvent.shiftKey) void submit(input); }} multiline placeholder="Ask for a story or change something..." placeholderTextColor={theme.textSecondary} style={[styles.input, { color: theme.text }]} /><Pressable onPress={() => submit(input)} style={[styles.sendButton, { backgroundColor: theme.accent }]}><SymbolView name="arrow.up" tintColor={theme.accentText} size={20} /></Pressable></View>
        </KeyboardAvoidingView>
      </SafeAreaView>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 }, safeArea: { flex: 1, maxWidth: 520, width: '100%', alignSelf: 'center', paddingHorizontal: 20, paddingBottom: 88 },
  header: { minHeight: 64, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }, headerTitle: { fontSize: 20, fontWeight: '800' }, headerActions: { flexDirection: 'row', gap: 8 }, iconButton: { width: 40, height: 40, borderRadius: 20, backgroundColor: '#302B4C', alignItems: 'center', justifyContent: 'center' },
  chatArea: { flex: 1 }, messages: { flex: 1 }, messagesContent: { paddingTop: 18, paddingBottom: 18, gap: 22 }, emptyWelcome: { alignItems: 'center', paddingVertical: 70, paddingHorizontal: 22 }, welcomeTitle: { fontSize: 29, lineHeight: 36, fontWeight: '800', textAlign: 'center' }, welcomeText: { textAlign: 'center', fontSize: 16, lineHeight: 24, marginTop: 12 }, messageBlock: { alignSelf: 'flex-start', maxWidth: '90%', gap: 12 }, userBlock: { alignSelf: 'flex-end', alignItems: 'flex-end' }, assistantText: { fontSize: 17, lineHeight: 26 }, userBubble: { backgroundColor: '#F7D77A', paddingHorizontal: 16, paddingVertical: 11, borderRadius: 20, fontSize: 16, lineHeight: 22 }, chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 }, chip: { borderRadius: 18, paddingHorizontal: 14, paddingVertical: 10, backgroundColor: '#25213D' }, storyCard: { borderRadius: 24, padding: 22, gap: 9, marginTop: 8 }, storyEyebrow: { color: '#F7D77A', fontSize: 10, fontWeight: '800', letterSpacing: 1.2 }, storyTitle: { fontSize: 28, lineHeight: 34, fontWeight: '800' }, storyPreview: { fontSize: 17, lineHeight: 28, marginTop: 10 }, storyActions: { flexDirection: 'row', alignItems: 'center', gap: 12, marginTop: 12 }, readButton: { flex: 1, minHeight: 50, borderRadius: 17, backgroundColor: '#F7D77A', alignItems: 'center', justifyContent: 'center' }, bookmarkButton: { width: 50, height: 50, borderRadius: 17, backgroundColor: '#302B4C', alignItems: 'center', justifyContent: 'center' }, thinking: { fontSize: 14 }, composer: { minHeight: 62, borderRadius: 22, marginBottom: 8, padding: 7, flexDirection: 'row', alignItems: 'flex-end', gap: 8 }, input: { flex: 1, paddingHorizontal: 14, paddingVertical: 12, maxHeight: 110, fontSize: 16 }, sendButton: { width: 46, height: 46, borderRadius: 17, alignItems: 'center', justifyContent: 'center' },
});
