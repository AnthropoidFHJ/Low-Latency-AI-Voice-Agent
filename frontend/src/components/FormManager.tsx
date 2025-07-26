'use client';

import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    FileText,
    Check,
    X,
    AlertCircle,
    Send,
    Eye,
    User,
    Mail,
    Phone,
    MessageCircle,
    Calendar,
    Building,
    Star
} from 'lucide-react';
import { useCurrentForm } from '../lib/store';
import { useVoiceAgent } from '../lib/voice-client';
import toast from 'react-hot-toast';

const fieldIcons: Record<string, React.ReactNode> = {
    name: <User className="w-4 h-4" />,
    first_name: <User className="w-4 h-4" />,
    last_name: <User className="w-4 h-4" />,
    email: <Mail className="w-4 h-4" />,
    phone: <Phone className="w-4 h-4" />,
    message: <MessageCircle className="w-4 h-4" />,
    feedback: <MessageCircle className="w-4 h-4" />,
    comments: <MessageCircle className="w-4 h-4" />,
    age: <Calendar className="w-4 h-4" />,
    company: <Building className="w-4 h-4" />,
    rating: <Star className="w-4 h-4" />,
};

const FormField: React.FC<{
    field: any;
    onManualEdit: (name: string, value: string) => void;
}> = ({ field, onManualEdit }) => {
    const [localValue, setLocalValue] = useState(field.value || '');
    const [isEditing, setIsEditing] = useState(false);

    useEffect(() => {
        setLocalValue(field.value || '');
    }, [field.value]);

    const handleSubmit = () => {
        if (localValue !== field.value) {
            onManualEdit(field.name, localValue);
            toast.success(`Updated ${field.name}`);
        }
        setIsEditing(false);
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        } else if (e.key === 'Escape') {
            setLocalValue(field.value || '');
            setIsEditing(false);
        }
    };

    const getFieldComponent = () => {
        if (field.type === 'textarea') {
            return (
                <textarea
                    value={localValue}
                    onChange={(e) => setLocalValue(e.target.value)}
                    onKeyDown={handleKeyPress}
                    className={`form-field resize-none ${field.filled ? 'success' : ''} ${field.error ? 'error' : ''}`}
                    placeholder={`Enter your ${field.name.replace('_', ' ')}...`}
                    rows={3}
                    disabled={!isEditing}
                />
            );
        }

        return (
            <input
                type={field.type === 'email' ? 'email' : field.type === 'tel' ? 'tel' : field.type === 'number' ? 'number' : 'text'}
                value={localValue}
                onChange={(e) => setLocalValue(e.target.value)}
                onKeyDown={handleKeyPress}
                className={`form-field ${field.filled ? 'success' : ''} ${field.error ? 'error' : ''}`}
                placeholder={`Enter your ${field.name.replace('_', ' ')}...`}
                disabled={!isEditing}
            />
        );
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-2"
        >
            <div className="flex items-center justify-between">
                <label className="flex items-center space-x-2 text-sm font-medium text-text-primary">
                    {fieldIcons[field.name] || <FileText className="w-4 h-4" />}
                    <span className="capitalize">
                        {field.name.replace('_', ' ')}
                        {field.required && <span className="text-voice-error ml-1">*</span>}
                    </span>
                </label>

                <div className="flex items-center space-x-2">
                    {field.filled && (
                        <Check className="w-4 h-4 text-form-success" />
                    )}
                    {field.error && (
                        <AlertCircle className="w-4 h-4 text-form-error" />
                    )}
                    <button
                        onClick={() => isEditing ? handleSubmit() : setIsEditing(true)}
                        className="text-xs text-text-accent hover:text-text-primary transition-colors"
                    >
                        {isEditing ? 'Save' : 'Edit'}
                    </button>
                </div>
            </div>

            {getFieldComponent()}

            {field.error && (
                <p className="text-xs text-form-error">{field.error}</p>
            )}

            {!isEditing && field.filled && (
                <p className="text-xs text-text-secondary">
                    Set via voice: "{field.value}"
                </p>
            )}
        </motion.div>
    );
};

const QuickFormActions: React.FC = () => {
    const { openForm } = useVoiceAgent();

    const formTypes = [
        { type: 'contact', label: 'Contact Form', icon: <Mail className="w-4 h-4" /> },
        { type: 'registration', label: 'Registration', icon: <User className="w-4 h-4" /> },
        { type: 'feedback', label: 'Feedback', icon: <MessageCircle className="w-4 h-4" /> },
        { type: 'survey', label: 'Survey', icon: <Star className="w-4 h-4" /> },
    ];

    const handleQuickOpen = (formType: string) => {
        openForm(formType);
        toast.success(`Opening ${formType} form...`);
    };

    return (
        <div className="glass-panel p-4">
            <h3 className="text-sm font-medium text-text-primary mb-3 flex items-center">
                <FileText className="w-4 h-4 mr-2" />
                Quick Open Forms
            </h3>
            <div className="grid grid-cols-2 gap-2">
                {formTypes.map((form) => (
                    <button
                        key={form.type}
                        onClick={() => handleQuickOpen(form.type)}
                        className="flex items-center space-x-2 p-2 rounded-lg bg-background-accent hover:bg-background-secondary transition-colors text-sm"
                    >
                        {form.icon}
                        <span>{form.label}</span>
                    </button>
                ))}
            </div>
            <p className="text-xs text-text-secondary mt-3">
                Or say: "I want to fill a contact form"
            </p>
        </div>
    );
};

export const FormManager: React.FC = () => {
    const currentForm = useCurrentForm();
    const { fillFormField, validateForm, submitForm } = useVoiceAgent();

    const [isValidating, setIsValidating] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleManualEdit = (fieldName: string, value: string) => {
        fillFormField(fieldName, value);
    };

    const handleValidate = async () => {
        setIsValidating(true);
        const success = validateForm();
        if (success) {
            toast.success('Validating form...');
        } else {
            toast.error('Failed to validate form');
        }
        setTimeout(() => setIsValidating(false), 1000);
    };

    const handleSubmit = async () => {
        if (!currentForm?.isValid) {
            toast.error('Please fill all required fields');
            return;
        }

        setIsSubmitting(true);
        const success = submitForm();
        if (success) {
            toast.success('Submitting form...');
        } else {
            toast.error('Failed to submit form');
        }
        setTimeout(() => setIsSubmitting(false), 2000);
    };

    if (!currentForm) {
        return (
            <div className="space-y-4">
                <QuickFormActions />

                <div className="glass-panel p-6 text-center">
                    <FileText className="w-12 h-12 text-text-secondary mx-auto mb-4" />
                    <h2 className="text-lg font-semibold text-text-primary mb-2">
                        No Form Open
                    </h2>
                    <p className="text-text-secondary mb-4">
                        Start a conversation and say "I want to fill a form" or use the quick actions above.
                    </p>
                    <div className="text-xs text-text-secondary space-y-1">
                        <p>💬 "I want to fill a contact form"</p>
                        <p>💬 "Open a registration form"</p>
                        <p>💬 "I need to give feedback"</p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {}
            <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass-panel p-4"
            >
                <div className="flex items-center justify-between">
                    <div>
                        <h2 className="text-lg font-semibold text-text-primary flex items-center">
                            <FileText className="w-5 h-5 mr-2" />
                            {currentForm.title}
                        </h2>
                        <p className="text-sm text-text-secondary">
                            Form ID: {currentForm.id}
                        </p>
                    </div>

                    <div className="text-right">
                        <div className={`text-sm font-medium ${currentForm.isValid ? 'text-form-success' : 'text-text-secondary'}`}>
                            {Math.round(currentForm.completionPercentage)}% Complete
                        </div>
                        <div className="w-20 h-2 bg-background-accent rounded-full mt-1">
                            <motion.div
                                className="h-full bg-voice-active rounded-full"
                                initial={{ width: 0 }}
                                animate={{ width: `${currentForm.completionPercentage}%` }}
                                transition={{ duration: 0.5 }}
                            />
                        </div>
                    </div>
                </div>
            </motion.div>

            {}
            <div className="glass-panel p-4">
                <h3 className="text-sm font-medium text-text-primary mb-4 flex items-center">
                    <Eye className="w-4 h-4 mr-2" />
                    Form Fields
                </h3>

                <div className="space-y-4">
                    {currentForm.fields.map((field, index) => (
                        <FormField
                            key={field.name}
                            field={field}
                            onManualEdit={handleManualEdit}
                        />
                    ))}
                </div>

                {}
                <div className="mt-6 p-3 bg-background-accent rounded-lg">
                    <p className="text-xs text-text-secondary mb-2">
                        💡 <strong>Voice Commands:</strong>
                    </p>
                    <div className="text-xs text-text-secondary space-y-1">
                        <p>• "My name is John Smith"</p>
                        <p>• "Set email to john@example.com"</p>
                        <p>• "The message is: Hello world"</p>
                        <p>• "Submit the form"</p>
                    </div>
                </div>
            </div>

            {}
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass-panel p-4"
            >
                <div className="flex space-x-3">
                    <button
                        onClick={handleValidate}
                        disabled={isValidating}
                        className="flex-1 flex items-center justify-center space-x-2 px-4 py-2 bg-voice-listening hover:bg-voice-listening/80 text-white rounded-lg transition-colors disabled:opacity-50"
                    >
                        <Eye className="w-4 h-4" />
                        <span>{isValidating ? 'Validating...' : 'Validate'}</span>
                    </button>

                    <button
                        onClick={handleSubmit}
                        disabled={!currentForm.isValid || isSubmitting}
                        className="flex-1 flex items-center justify-center space-x-2 px-4 py-2 bg-voice-active hover:bg-voice-active/80 text-white rounded-lg transition-colors disabled:opacity-50"
                    >
                        <Send className="w-4 h-4" />
                        <span>{isSubmitting ? 'Submitting...' : 'Submit'}</span>
                    </button>
                </div>

                <div className="mt-3 text-center">
                    <p className="text-xs text-text-secondary">
                        💬 Or say: "Validate the form" or "Submit the form"
                    </p>
                </div>
            </motion.div>

            {}
            <AnimatePresence>
                {currentForm.isValid && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        className="glass-panel p-4 border border-form-success/30"
                    >
                        <div className="flex items-center space-x-2 text-form-success">
                            <Check className="w-5 h-5" />
                            <span className="font-medium">Form Ready to Submit</span>
                        </div>
                        <p className="text-sm text-text-secondary mt-1">
                            All required fields are filled and valid.
                        </p>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};
