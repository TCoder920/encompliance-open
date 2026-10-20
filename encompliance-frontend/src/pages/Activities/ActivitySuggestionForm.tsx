/*
Description: A form component for submitting activity suggestions.
Purpose: Captures user input for a new activity idea and sends it to the backend.
*/
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { submitActivitySuggestion } from '../../services/activitySuggestionService';
import DateTimePicker from '../../components/ui/DateTimePicker';

const ActivitySuggestionForm = () => {
    const navigate = useNavigate();
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [category, setCategory] = useState('');
    const [location, setLocation] = useState('');
    const [suggestedDate, setSuggestedDate] = useState('');
    const [estimatedDuration, setEstimatedDuration] = useState('');
    const [message, setMessage] = useState('');

    /**
     * Handles form submission, sending the suggestion data to the service.
     */
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setMessage('');
        try {
            await submitActivitySuggestion({
                title,
                description,
                category,
                location,
                suggested_date: suggestedDate || undefined,
                estimated_duration_minutes: estimatedDuration ? parseInt(estimatedDuration) : undefined,
            });
            // Show success message briefly then redirect
            setMessage('Suggestion submitted successfully!');
            setTimeout(() => {
                navigate('/activities');
            }, 1500);
        } catch (error) {
            console.error('Failed to submit suggestion', error);
            setMessage('Failed to submit suggestion. Please try again.');
        }
    };

    return (
        <div className="max-w-2xl mx-auto">
            <form onSubmit={handleSubmit} className="space-y-6 p-6 bg-white dark:bg-dark-surface rounded-lg shadow-md border border-gray-200 dark:border-gray-700">
                <div className="text-center mb-6">
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Suggest an Activity</h2>
                    <p className="text-gray-600 dark:text-gray-400 mt-2">
                        Share your ideas for new facility activities that could benefit everyone.
                    </p>
                </div>

                {message && (
                    <div
                        className={`text-center p-3 rounded-lg font-medium 
                            ${message.toLowerCase().includes('success')
                                ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                                : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'}`}
                    >
                        {message}
                    </div>
                )}

                <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Activity Title *
                    </label>
                    <input
                        type="text"
                        className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        placeholder="What would you like to call this activity?"
                        required
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Description
                    </label>
                    <textarea
                        className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        rows={4}
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        placeholder="Describe the activity, what it involves, and why it would be beneficial..."
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Category
                    </label>
                    <select
                        className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        value={category}
                        onChange={(e) => setCategory(e.target.value)}
                    >
                        <option value="">Select a category</option>
                        <option value="wellness">Wellness & Health</option>
                        <option value="training">Training & Education</option>
                        <option value="social">Social & Team Building</option>
                        <option value="recreational">Recreational</option>
                        <option value="community">Community Service</option>
                        <option value="professional">Professional Development</option>
                        <option value="other">Other</option>
                    </select>
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Location
                    </label>
                    <input
                        type="text"
                        className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        value={location}
                        onChange={(e) => setLocation(e.target.value)}
                        placeholder="Where should this activity take place?"
                    />
                </div>

                <DateTimePicker
                    label="Suggested Date & Time"
                    value={suggestedDate}
                    onChange={setSuggestedDate}
                    placeholder="When would be ideal for this activity?"
                />

                <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Estimated Duration (minutes)
                    </label>
                    <input
                        type="number"
                        min="15"
                        max="480"
                        className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        value={estimatedDuration}
                        onChange={(e) => setEstimatedDuration(e.target.value)}
                        placeholder="How long should this activity last?"
                    />
                </div>

                <button 
                    type="submit" 
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition-colors focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                >
                    Submit Suggestion
                </button>
            </form>
        </div>
    );
};

export default ActivitySuggestionForm; 