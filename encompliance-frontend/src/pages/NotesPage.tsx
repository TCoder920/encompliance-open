/**
 * Description: Notes page for the EnCompliance application.
 * Purpose: Provides a container for the Notes component with appropriate page layout.
 * This is a premium feature with freemium preview functionality for Free tier users.
 */

import React, { useState, useEffect } from 'react';
import { Plus, Search, Filter, StickyNote, Pin, Archive, Edit, Trash2, ArchiveX, Trash } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { Tier, getTierFromSubscriptionStatus } from '../utils/tiers';
import { canUseFeature } from '../utils/accessControl';
import { SAMPLE_NOTES } from '../utils/previewData';
import FeaturePreview from '../components/ui/FeaturePreview';
import api from '../services/api';

interface Note {
  id: string | number;
  title: string;
  content: string;
  created_at: string;
  updated_at: string;
  is_pinned: boolean;
  is_archived: boolean;
  isPreview?: boolean;
  user_id?: number; // Optional field for backend compatibility
}

interface BulkOperationResponse {
  count: number;
  message: string;
}

const NotesPage: React.FC = () => {
  const { user } = useAuth();
  const [notes, setNotes] = useState<Note[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showArchived, setShowArchived] = useState(false);
  const [selectedNote, setSelectedNote] = useState<Note | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [showBulkActions, setShowBulkActions] = useState(false);

  const userTier = getTierFromSubscriptionStatus(user?.subscription_status);
  const canUse = canUseFeature(userTier, 'notes');

  // Fetch notes
  useEffect(() => {
    fetchNotes();
  }, [userTier]);

  // Close bulk actions dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Element;
      if (!target.closest('.bulk-actions-container')) {
        setShowBulkActions(false);
      }
    };

    if (showBulkActions) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [showBulkActions]);

  const fetchNotes = async () => {
    try {
      setIsLoading(true);
      
      if (canUse) {
        // Fetch real notes for paid users - Get all notes and filter on frontend
        const response = await api.get('/notes/');
        setNotes(response.data.notes || []);
      } else {
        // Use sample notes for free users
        setNotes(SAMPLE_NOTES);
      }
      
      setError(null);
    } catch (err) {
      setError('Failed to load notes');
      console.error('Error fetching notes:', err);
      
      // Fallback to sample data on error
      if (!canUse) {
        setNotes(SAMPLE_NOTES);
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Filter notes based on search and archive status
  const filteredNotes = notes.filter(note => {
    const matchesSearch = note.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         note.content.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesArchive = showArchived ? note.is_archived : !note.is_archived;
    return matchesSearch && matchesArchive;
  });

  // Sort notes: pinned first, then by updated date
  const sortedNotes = filteredNotes.sort((a, b) => {
    if (a.is_pinned && !b.is_pinned) return -1;
    if (!a.is_pinned && b.is_pinned) return 1;
    return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
  });

  const handleCreateNote = () => {
    // For preview mode, this will be intercepted by FeaturePreview
    if (!canUse) return;
    
    const newNote: Note = {
      id: Date.now().toString(),
      title: 'New Note',
      content: '',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      is_pinned: false,
      is_archived: false,
    };
    setSelectedNote(newNote);
    setIsEditing(true);
  };

  const handleEditNote = (note: Note) => {
    // For preview mode, this will be intercepted by FeaturePreview
    if (!canUse) return;
    
    setSelectedNote(note);
    setIsEditing(true);
  };

  const handleSaveNote = async () => {
    // For preview mode, this will be intercepted by FeaturePreview
    if (!canUse || !selectedNote) return;

    try {
      if (selectedNote.id && notes.find(n => n.id.toString() === selectedNote.id.toString())) {
        // Update existing note - Note: Individual note endpoints don't need trailing slash
        await api.put(`/notes/${selectedNote.id}`, selectedNote);
      } else {
        // Create new note - FIX: Add trailing slash
        await api.post('/notes/', selectedNote);
      }
      
      setIsEditing(false);
      setSelectedNote(null);
      fetchNotes();
    } catch (err) {
      setError('Failed to save note');
      console.error('Error saving note:', err);
    }
  };

  const handleDeleteNote = async (noteId: string) => {
    // For preview mode, this will be intercepted by FeaturePreview
    if (!canUse) return;

    try {
      // Individual note endpoints don't need trailing slash
      await api.delete(`/notes/${noteId}`);
      fetchNotes();
    } catch (err) {
      setError('Failed to delete note');
      console.error('Error deleting note:', err);
    }
  };

  const handleTogglePin = async (noteId: string) => {
    // For preview mode, this will be intercepted by FeaturePreview
    if (!canUse) return;

    try {
      const note = notes.find(n => n.id.toString() === noteId);
      if (!note) return;

      // Individual note action endpoints don't need trailing slash
      if (note.is_pinned) {
        await api.post(`/notes/${noteId}/unpin`);
      } else {
        await api.post(`/notes/${noteId}/pin`);
      }
      fetchNotes();
    } catch (err) {
      setError('Failed to toggle pin');
      console.error('Error toggling pin:', err);
    }
  };

  const handleToggleArchive = async (noteId: string) => {
    // For preview mode, this will be intercepted by FeaturePreview
    if (!canUse) return;

    try {
      const note = notes.find(n => n.id.toString() === noteId);
      if (!note) return;

      // Individual note action endpoints don't need trailing slash
      if (note.is_archived) {
        await api.post(`/notes/${noteId}/unarchive`);
      } else {
        await api.post(`/notes/${noteId}/archive`);
      }
      fetchNotes();
    } catch (err) {
      setError('Failed to toggle archive');
      console.error('Error toggling archive:', err);
    }
  };

  const handleArchiveAll = async () => {
    // For preview mode, this will be intercepted by FeaturePreview
    if (!canUse) return;

    if (!confirm('Are you sure you want to archive all notes? This action can be undone.')) {
      return;
    }

    try {
      // Bulk endpoints don't need trailing slash
      const response = await api.post<BulkOperationResponse>('/notes/bulk/archive-all');
      setError(null);
      fetchNotes();
      setShowBulkActions(false);
      // Show success message
      console.log(response.data.message);
    } catch (err) {
      setError('Failed to archive all notes');
      console.error('Error archiving all notes:', err);
    }
  };

  const handleDeleteAll = async (archivedOnly: boolean = false) => {
    // For preview mode, this will be intercepted by FeaturePreview
    if (!canUse) return;

    const confirmMessage = archivedOnly 
      ? 'Are you sure you want to permanently delete all archived notes? This action cannot be undone.'
      : 'Are you sure you want to permanently delete ALL notes? This action cannot be undone.';
    
    if (!confirm(confirmMessage)) {
      return;
    }

    try {
      // Bulk endpoints don't need trailing slash
      const response = await api.delete<BulkOperationResponse>(`/notes/bulk/delete-all?archived_only=${archivedOnly}`);
      setError(null);
      fetchNotes();
      setShowBulkActions(false);
      // Show success message
      console.log(response.data.message);
    } catch (err) {
      setError(`Failed to delete ${archivedOnly ? 'archived ' : ''}notes`);
      console.error('Error deleting notes:', err);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Preview content for free users
  const previewContent = (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-800 dark:text-white flex items-center">
          <StickyNote className="mr-3 h-8 w-8" />
          Compliance Notes
        </h1>
        <button className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center hover:bg-blue-700 transition-colors">
          <Plus className="mr-2 h-4 w-4" />
          New Note
        </button>
      </div>

      <p className="text-gray-600 dark:text-gray-300">
        Organize your compliance documentation, checklists, and important notes in one place.
      </p>

      {/* Search and Filter */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <input
            type="text"
            placeholder="Search notes..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
          />
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowArchived(!showArchived)}
            className={`px-4 py-2 rounded-lg flex items-center transition-colors ${
              showArchived 
                ? 'bg-gray-600 text-white' 
                : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            <Archive className="mr-2 h-4 w-4" />
            {showArchived ? 'Hide Archived' : 'Show Archived'}
          </button>
          
          {/* Bulk Actions Button */}
          <div className="relative bulk-actions-container">
            <button
              onClick={() => setShowBulkActions(!showBulkActions)}
              className="px-4 py-2 rounded-lg flex items-center transition-colors bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600"
            >
              <Filter className="mr-2 h-4 w-4" />
              Bulk Actions
            </button>
            
            {/* Bulk Actions Dropdown */}
            {showBulkActions && (
              <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-10">
                <div className="py-1">
                  <button
                    onClick={handleArchiveAll}
                    className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center"
                  >
                    <ArchiveX className="mr-2 h-4 w-4" />
                    Archive All Notes
                  </button>
                  <button
                    onClick={() => handleDeleteAll(false)}
                    className="w-full px-4 py-2 text-left text-sm text-red-600 dark:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center"
                  >
                    <Trash className="mr-2 h-4 w-4" />
                    Delete All Notes
                  </button>
                  <button
                    onClick={() => handleDeleteAll(true)}
                    className="w-full px-4 py-2 text-left text-sm text-red-600 dark:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center"
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    Delete Archived Notes
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Notes Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {isLoading ? (
          Array.from({ length: 6 }).map((_, index) => (
            <div key={index} className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 animate-pulse">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded mb-1"></div>
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded mb-1"></div>
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-2/3"></div>
            </div>
          ))
        ) : (
          sortedNotes.map((note) => (
            <div
              key={note.id}
              className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow cursor-pointer relative"
            >
              {note.is_pinned && (
                <Pin className="absolute top-2 left-2 h-4 w-4 text-yellow-500" />
              )}
              
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2 pr-6 pl-6">
                {note.title}
              </h3>
              
              <p className="text-gray-600 dark:text-gray-300 text-sm mb-3 line-clamp-3">
                {note.content}
              </p>
              
              <div className="flex justify-between items-center text-xs text-gray-500 dark:text-gray-400">
                <span>{formatDate(note.updated_at)}</span>
                {note.isPreview && (
                  <span className="bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-1 rounded">
                    Sample
                  </span>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {error && (
        <div className="bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-800 text-red-800 dark:text-red-300 px-4 py-3 rounded">
          {error}
        </div>
      )}
    </div>
  );

  // Main content for paid users
  const mainContent = (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-800 dark:text-white flex items-center">
          <StickyNote className="mr-3 h-8 w-8" />
          Compliance Notes
        </h1>
        <button 
          onClick={handleCreateNote}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center hover:bg-blue-700 transition-colors"
        >
          <Plus className="mr-2 h-4 w-4" />
          New Note
        </button>
      </div>

      <p className="text-gray-600 dark:text-gray-300">
        Organize your compliance documentation, checklists, and important notes in one place.
      </p>

      {/* Search and Filter */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <input
            type="text"
            placeholder="Search notes..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
          />
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowArchived(!showArchived)}
            className={`px-4 py-2 rounded-lg flex items-center transition-colors ${
              showArchived 
                ? 'bg-gray-600 text-white' 
                : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            <Archive className="mr-2 h-4 w-4" />
            {showArchived ? 'Hide Archived' : 'Show Archived'}
          </button>
          
          {/* Bulk Actions Button */}
          <div className="relative bulk-actions-container">
            <button
              onClick={() => setShowBulkActions(!showBulkActions)}
              className="px-4 py-2 rounded-lg flex items-center transition-colors bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600"
            >
              <Filter className="mr-2 h-4 w-4" />
              Bulk Actions
            </button>
            
            {/* Bulk Actions Dropdown */}
            {showBulkActions && (
              <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-10">
                <div className="py-1">
                  <button
                    onClick={handleArchiveAll}
                    className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center"
                  >
                    <ArchiveX className="mr-2 h-4 w-4" />
                    Archive All Notes
                  </button>
                  <button
                    onClick={() => handleDeleteAll(false)}
                    className="w-full px-4 py-2 text-left text-sm text-red-600 dark:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center"
                  >
                    <Trash className="mr-2 h-4 w-4" />
                    Delete All Notes
                  </button>
                  <button
                    onClick={() => handleDeleteAll(true)}
                    className="w-full px-4 py-2 text-left text-sm text-red-600 dark:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center"
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    Delete Archived Notes
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Notes Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {isLoading ? (
          Array.from({ length: 6 }).map((_, index) => (
            <div key={index} className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 animate-pulse">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded mb-1"></div>
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded mb-1"></div>
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-2/3"></div>
            </div>
          ))
        ) : (
          sortedNotes.map((note) => (
            <div
              key={note.id}
              className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow cursor-pointer relative group"
              onClick={() => handleEditNote(note)}
            >
              {/* Static pin icon when pinned - positioned separately to avoid overlap */}
              {note.is_pinned && (
                <Pin className="absolute top-2 left-2 h-4 w-4 text-yellow-500" />
              )}
              
              {/* Action buttons - positioned in top-right corner */}
              <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex space-x-1">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleTogglePin(note.id.toString());
                  }}
                  className={`p-1 rounded ${note.is_pinned ? 'text-yellow-500' : 'text-gray-400 hover:text-yellow-500'}`}
                >
                  <Pin className="h-3 w-3" />
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleToggleArchive(note.id.toString());
                  }}
                  className="p-1 rounded text-gray-400 hover:text-blue-500"
                >
                  <Archive className="h-3 w-3" />
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteNote(note.id.toString());
                  }}
                  className="p-1 rounded text-gray-400 hover:text-red-500"
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              </div>
              
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2 pr-6 pl-6">
                {note.title}
              </h3>
              
              <p className="text-gray-600 dark:text-gray-300 text-sm mb-3 line-clamp-3">
                {note.content}
              </p>
              
              <div className="flex justify-between items-center text-xs text-gray-500 dark:text-gray-400">
                <span>{formatDate(note.updated_at)}</span>
                {note.is_archived && (
                  <span className="bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 px-2 py-1 rounded">
                    Archived
                  </span>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {error && (
        <div className="bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-800 text-red-800 dark:text-red-300 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Edit Modal */}
      {isEditing && selectedNote && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                {selectedNote.id && notes.find(n => n.id.toString() === selectedNote.id.toString()) ? 'Edit Note' : 'New Note'}
              </h3>
              <button
                onClick={() => {
                  setIsEditing(false);
                  setSelectedNote(null);
                }}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <Plus className="h-6 w-6 rotate-45" />
              </button>
            </div>
            
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Title
                </label>
                <input
                  type="text"
                  value={selectedNote.title}
                  onChange={(e) => setSelectedNote({...selectedNote, title: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="Note title"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Content
                </label>
                <textarea
                  value={selectedNote.content}
                  onChange={(e) => setSelectedNote({...selectedNote, content: e.target.value})}
                  rows={12}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="Write your note content here..."
                />
              </div>
            </div>
            
            <div className="flex justify-end space-x-3 p-6 border-t border-gray-200 dark:border-gray-700">
              <button
                onClick={() => {
                  setIsEditing(false);
                  setSelectedNote(null);
                }}
                className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveNote}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Save Note
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="bg-white dark:bg-dark-surface rounded-lg shadow-md p-6">
        <FeaturePreview
          featureKey="notes"
          previewContent={previewContent}
          showPreviewBadge={true}
        >
          {mainContent}
        </FeaturePreview>
      </div>
    </div>
  );
};

export default NotesPage; 