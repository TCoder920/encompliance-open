/*
Description: A modal component for handling user signups for an activity.
Purpose: Provides a dialog for users to confirm their registration and add optional notes.
*/
import React, { useState } from 'react';

interface ActivitySignupModalProps {
    activityId: string;
    onClose: () => void;
    onSignup: (notes: string) => void;
}

const ActivitySignupModal: React.FC<ActivitySignupModalProps> = ({ activityId, onClose, onSignup }) => {
    const [notes, setNotes] = useState('');

    const handleSignup = () => {
        onSignup(notes);
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center">
            <div className="bg-white p-6 rounded-lg shadow-xl">
                <h2 className="text-xl font-bold mb-4">Sign Up for Activity</h2>
                <textarea
                    className="w-full p-2 border rounded mb-4"
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="Optional notes..."
                />
                <div className="flex justify-end space-x-4">
                    <button onClick={onClose} className="bg-gray-300 hover:bg-gray-400 text-black font-bold py-2 px-4 rounded">Cancel</button>
                    <button onClick={handleSignup} className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">Confirm Signup</button>
                </div>
            </div>
        </div>
    );
};

export default ActivitySignupModal; 