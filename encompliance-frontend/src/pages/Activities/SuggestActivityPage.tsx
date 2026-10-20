/*
Description: A dedicated page for users to submit activity suggestions.
Purpose: Provides a user-friendly form for creating and submitting activity ideas for facility administrator review.
*/
import React from 'react';
import ActivitySuggestionForm from './ActivitySuggestionForm';

const SuggestActivityPage = () => {
    return (
        <div className="container mx-auto px-4 py-8">
            <h1 className="text-2xl font-bold mb-4">Suggest an Activity</h1>
            <p className="mb-6">Have an idea for a fun or useful activity for the facility? Fill out the form below to submit it for review.</p>
            <ActivitySuggestionForm />
        </div>
    );
};

export default SuggestActivityPage; 