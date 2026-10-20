/*
Description: A card component for displaying a summary of a single facility activity.
Purpose: Used to render individual activities in a list, showing key details and providing a signup mechanism.
*/
import React, { useState } from 'react';
import { Activity } from '../../services/activityService';
import ActivitySignupModal from './ActivitySignupModal';
import EditActivityModal from './EditActivityModal';
import { signupForActivity } from '../../services/activityService';
import { Calendar, Clock, MapPin, Users } from 'lucide-react';

interface ActivityCardProps {
    activity: Activity;
    isAdmin?: boolean;
    onUpdate?: () => void;
}

const ActivityCard: React.FC<ActivityCardProps> = ({ activity, isAdmin = false, onUpdate }) => {
    const [isSignupModalOpen, setSignupModalOpen] = useState(false);
    const [isEditModalOpen, setEditModalOpen] = useState(false);

    /**
     * Handles the signup logic when a user confirms registration through the modal.
     * @param notes - Optional notes from the user.
     */
    const handleSignup = async (notes: string) => {
        try {
            await signupForActivity({ calendar_event_id: activity.id, notes });
            setSignupModalOpen(false);
            // Optionally, refresh activity data or show a success message
        } catch (error) {
            console.error("Failed to sign up for activity", error);
            // Handle error, e.g., show an error message
        }
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



    return (
        <div 
            className={`bg-white dark:bg-dark-surface rounded-lg shadow-md border border-gray-200 dark:border-gray-700 overflow-hidden transition-all duration-200 ${isAdmin ? 'hover:shadow-lg hover:border-blue-300 dark:hover:border-blue-600 cursor-pointer' : ''}`}
            onClick={isAdmin ? () => setEditModalOpen(true) : undefined}
        >
            {/* Header */}
            <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                    <div>
                        <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
                            {activity.title}
                        </h3>
                        {activity.activityCategory && (
                            <span className="inline-block bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs px-2 py-1 rounded-full mt-1">
                                {activity.activityCategory}
                            </span>
                        )}
                    </div>
                </div>

                {/* Description */}
                {activity.description && (
                    <p className="text-gray-600 dark:text-gray-400 mb-4 line-clamp-2">
                        {activity.description}
                    </p>
                )}

                {/* Event Details */}
                <div className="space-y-2 mb-4">
                    <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                        <Clock className="h-4 w-4 mr-2 text-blue-500" />
                        <span>{formatDate(activity.start)} - {formatDate(activity.end)}</span>
                    </div>
                    
                    {activity.location && (
                        <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                            <MapPin className="h-4 w-4 mr-2 text-blue-500" />
                            <span>{activity.location}</span>
                        </div>
                    )}
                    
                    {activity.requiresSignup && (
                        <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                            <Users className="h-4 w-4 mr-2 text-blue-500" />
                            <span>
                                {activity.currentParticipants} / {activity.maxParticipants || 'Unlimited'} participants
                            </span>
                        </div>
                    )}
                </div>

                {/* Status Badge */}
                <div className="flex items-center justify-between">
                    <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${
                        activity.activityStatus === 'planned' 
                            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                            : activity.activityStatus === 'active'
                            ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                            : activity.activityStatus === 'completed'
                            ? 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
                            : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                    }`}>
                        {activity.activityStatus}
                    </span>

                    {/* Signup Button */}
                    {activity.requiresSignup && !isAdmin && (
                        <button 
                            onClick={(e) => {
                                e.stopPropagation();
                                setSignupModalOpen(true);
                            }} 
                            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
                        >
                            Sign Up
                        </button>
                    )}
                </div>
            </div>

            {/* Modals */}
            {isSignupModalOpen && (
                <ActivitySignupModal
                    activityId={activity.id}
                    onClose={() => setSignupModalOpen(false)}
                    onSignup={handleSignup}
                />
            )}
            
            {isEditModalOpen && (
                <EditActivityModal
                    activity={activity}
                    isOpen={isEditModalOpen}
                    onClose={() => setEditModalOpen(false)}
                    onUpdate={() => {
                        onUpdate?.();
                        setEditModalOpen(false);
                    }}
                />
            )}
        </div>
    );
};

export default ActivityCard; 