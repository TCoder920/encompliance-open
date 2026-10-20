/*
Description: Main page for viewing facility activities and suggestions.
Purpose: Displays upcoming activities, recent suggestions, and provides navigation to suggest new activities.
*/
import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Activity, getActivities } from '../../services/activityService';
import { ActivitySuggestion, getFacilitySuggestions, getMySuggestions, getAllSuggestions } from '../../services/activitySuggestionService';
import { Calendar, Plus, Clock, Users, MapPin, Lightbulb, Star, X } from 'lucide-react';
import ActivityCard from './ActivityCard';
import ActivitySuggestionCard from './ActivitySuggestionCard';
import EditActivitySuggestionModal from './EditActivitySuggestionModal';
import { useAuth } from '../../contexts/AuthContext';

const ActivityCalendar = () => {
    const { user } = useAuth();
    const [activities, setActivities] = useState<Activity[]>([]);
    const [suggestions, setSuggestions] = useState<ActivitySuggestion[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<'activities' | 'suggestions' | 'rejected'>('activities');
    const [editingSuggestion, setEditingSuggestion] = useState<ActivitySuggestion | null>(null);
    
    // Get current user info from auth context
    const currentUserId = user?.id || null;
    const isAdmin = !!user?.user_role && user.user_role.toString().toLowerCase().includes('admin');
    
    // Debug logging
    console.log('Current user:', user);
    console.log('User ID:', currentUserId);
    console.log('Is Admin:', isAdmin);
    console.log('User role:', user?.user_role);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                
                // Fetch activities
                const activitiesData = await getActivities();
                setActivities(activitiesData);

                // Fetch suggestions - try development endpoint first, then facility-wide, then user's suggestions
                try {
                    console.log('Attempting to fetch all suggestions (development)...');
                    const allSuggestions = await getAllSuggestions();
                    console.log('All suggestions fetched:', allSuggestions);
                    setSuggestions(allSuggestions);
                } catch (allError) {
                    console.log('All suggestions failed, trying facility suggestions:', allError);
                    try {
                        console.log('Attempting to fetch facility suggestions...');
                        const facilitySuggestions = await getFacilitySuggestions();
                        console.log('Facility suggestions fetched:', facilitySuggestions);
                        setSuggestions(facilitySuggestions);
                    } catch (facilityError) {
                        // If user doesn't have admin privileges, fetch their own suggestions
                        console.log('Facility suggestions failed, trying user suggestions:', facilityError);
                        try {
                            const userSuggestions = await getMySuggestions();
                            console.log('User suggestions fetched:', userSuggestions);
                            setSuggestions(userSuggestions);
                        } catch (userError) {
                            console.error('Failed to fetch user suggestions:', userError);
                            setSuggestions([]);
                        }
                    }
                }
                
            } catch (err) {
                setError('Failed to fetch activities and suggestions.');
                console.error('Error fetching data:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    const handleSuggestionUpdate = () => {
        // Refetch suggestions when they're updated
        const fetchSuggestions = async () => {
            try {
                const allSuggestions = await getAllSuggestions();
                setSuggestions(allSuggestions);
            } catch (error) {
                console.error('Failed to refetch suggestions:', error);
            }
        };
        fetchSuggestions();
    };

    const handleEditSuggestion = (suggestion: ActivitySuggestion) => {
        setEditingSuggestion(suggestion);
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const getCategoryIcon = (category?: string) => {
        switch (category?.toLowerCase()) {
            case 'wellness': return '🧘';
            case 'training': return '📚';
            case 'social': return '🤝';
            case 'recreational': return '🎮';
            case 'community': return '🌟';
            case 'professional': return '💼';
            default: return '📅';
        }
    };

    const getStatusColor = (status: string) => {
        switch (status.toLowerCase()) {
            case 'approved': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
            case 'pending': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
            case 'rejected': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
            case 'implemented': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
            default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
        }
    };

    if (loading) {
        return (
            <div className="container mx-auto px-4 py-8">
                <div className="flex justify-center items-center h-64">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="container mx-auto px-4 py-8">
                <div className="bg-red-100 dark:bg-red-900 border border-red-400 dark:border-red-700 text-red-700 dark:text-red-200 px-4 py-3 rounded">
                    {error}
                </div>
            </div>
        );
    }

    return (
        <div className="container mx-auto px-4 py-8">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center">
                        <Calendar className="h-8 w-8 mr-3 text-blue-600" />
                        Activity Center
                    </h1>
                    <p className="text-gray-600 dark:text-gray-400 mt-2">
                        Discover upcoming activities and share your ideas for new ones
                    </p>
                </div>
                <Link 
                    to="/activities/suggest" 
                    className="mt-4 md:mt-0 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors flex items-center space-x-2 shadow-md"
                >
                    <Plus className="h-5 w-5" />
                    <span>Suggest Activity</span>
                </Link>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <button 
                    onClick={() => setActiveTab('activities')}
                    className={`bg-white dark:bg-dark-surface rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700 transition-all duration-200 hover:shadow-lg hover:border-blue-300 dark:hover:border-blue-600 text-left ${
                        activeTab === 'activities' ? 'ring-2 ring-blue-500 border-blue-500' : ''
                    }`}
                >
                    <div className="flex items-center">
                        <div className="p-3 rounded-full bg-blue-100 dark:bg-blue-900">
                            <Calendar className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                        </div>
                        <div className="ml-4">
                            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Upcoming Activities</p>
                            <p className="text-2xl font-bold text-gray-900 dark:text-white">{activities.length}</p>
                        </div>
                    </div>
                </button>
                
                <button 
                    onClick={() => setActiveTab('suggestions')}
                    className={`bg-white dark:bg-dark-surface rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700 transition-all duration-200 hover:shadow-lg hover:border-blue-300 dark:hover:border-blue-600 text-left ${
                        activeTab === 'suggestions' ? 'ring-2 ring-blue-500 border-blue-500' : ''
                    }`}
                >
                    <div className="flex items-center">
                        <div className="p-3 rounded-full bg-yellow-100 dark:bg-yellow-900">
                            <Lightbulb className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
                        </div>
                        <div className="ml-4">
                            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Pending Suggestions</p>
                            <p className="text-2xl font-bold text-gray-900 dark:text-white">
                                {suggestions.filter(s => s.status === 'pending').length}
                            </p>
                        </div>
                    </div>
                </button>
                
                <button 
                    onClick={() => setActiveTab('rejected')}
                    className={`bg-white dark:bg-dark-surface rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700 transition-all duration-200 hover:shadow-lg hover:border-blue-300 dark:hover:border-blue-600 text-left ${
                        activeTab === 'rejected' ? 'ring-2 ring-blue-500 border-blue-500' : ''
                    }`}
                >
                    <div className="flex items-center">
                        <div className="p-3 rounded-full bg-red-100 dark:bg-red-900">
                            <X className="h-6 w-6 text-red-600 dark:text-red-400" />
                        </div>
                        <div className="ml-4">
                            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Rejected Suggestions</p>
                            <p className="text-2xl font-bold text-gray-900 dark:text-white">
                                {suggestions.filter(s => s.status === 'rejected').length}
                            </p>
                        </div>
                    </div>
                </button>
            </div>



            {/* Content */}
            {activeTab === 'activities' ? (
                <div>
                    {activities.length === 0 ? (
                        <div className="text-center py-12">
                            <Calendar className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">No Activities Scheduled</h3>
                            <p className="text-gray-600 dark:text-gray-400">
                                There are no upcoming activities at the moment. Use the "Suggest Activity" button above to propose new activities.
                            </p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {activities.map(activity => (
                                <ActivityCard 
                                    key={activity.id} 
                                    activity={activity} 
                                    isAdmin={isAdmin}
                                    onUpdate={() => {
                                        // Refetch activities when they're updated
                                        const fetchActivities = async () => {
                                            try {
                                                const activitiesData = await getActivities();
                                                setActivities(activitiesData);
                                            } catch (error) {
                                                console.error('Failed to refetch activities:', error);
                                            }
                                        };
                                        fetchActivities();
                                    }}
                                />
                            ))}
                        </div>
                    )}
                </div>
            ) : activeTab === 'suggestions' ? (
                <div>
                    {suggestions.filter(s => s.status === 'pending').length === 0 ? (
                        <div className="text-center py-12">
                            <Lightbulb className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">No Pending Suggestions</h3>
                            <p className="text-gray-600 dark:text-gray-400">
                                All suggestions have been reviewed! Use the "Suggest Activity" button above to propose new activities.
                            </p>
                        </div>
                    ) : (
                        <div className="space-y-6">
                            {suggestions.filter(s => s.status === 'pending').map(suggestion => (
                                <ActivitySuggestionCard
                                    key={suggestion.id}
                                    suggestion={suggestion}
                                    currentUserId={currentUserId || undefined}
                                    isAdmin={isAdmin}
                                    onUpdate={handleSuggestionUpdate}
                                    onEdit={handleEditSuggestion}
                                />
                            ))}
                        </div>
                    )}
                </div>
            ) : (
                <div>
                    {suggestions.filter(s => s.status === 'rejected').length === 0 ? (
                        <div className="text-center py-12">
                            <X className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">No Rejected Suggestions</h3>
                            <p className="text-gray-600 dark:text-gray-400">
                                No suggestions have been rejected yet.
                            </p>
                        </div>
                    ) : (
                        <div className="space-y-6">
                            {suggestions.filter(s => s.status === 'rejected').map(suggestion => (
                                <ActivitySuggestionCard
                                    key={suggestion.id}
                                    suggestion={suggestion}
                                    currentUserId={currentUserId || undefined}
                                    isAdmin={isAdmin}
                                    onUpdate={handleSuggestionUpdate}
                                    onEdit={handleEditSuggestion}
                                />
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* Edit Modal */}
            {editingSuggestion && (
                <EditActivitySuggestionModal
                    suggestion={editingSuggestion}
                    isOpen={!!editingSuggestion}
                    onClose={() => setEditingSuggestion(null)}
                    onUpdate={handleSuggestionUpdate}
                />
            )}
        </div>
    );
};

export default ActivityCalendar; 