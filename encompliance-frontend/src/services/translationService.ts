import api from './api';

/*
  Description: Translation service hitting the backend LibreTranslate proxy.
*/

export interface TranslationResponse {
  translated_text: string;
  detected_source: string;
}

export const translationService = {
  async translate(text: string, targetLanguage = 'es', sourceLanguage = 'en'): Promise<string> {
    const response = await api.post<TranslationResponse>('/translation', {
      text,
      target_language: targetLanguage,
      source_language: sourceLanguage,
    });
    return response.data.translated_text;
  },

  async translateBulk(phrases: string[], targetLanguage = 'es', sourceLanguage = 'en'): Promise<string[]> {
    const results: string[] = [];
    for (const phrase of phrases) {
      try {
        const translated = await translationService.translate(phrase, targetLanguage, sourceLanguage);
        results.push(translated);
      } catch {
        results.push(phrase);
      }
    }
    return results;
  },
};

export default translationService;

