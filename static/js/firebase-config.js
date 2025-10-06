// Firebase configuration for Fraction Ball LMS
// This file configures Firebase for frontend authentication

import { initializeApp } from 'firebase/app';
import { getAuth, connectAuthEmulator } from 'firebase/auth';
import { getStorage, connectStorageEmulator } from 'firebase/storage';
import { getAnalytics } from 'firebase/analytics';

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyAelVAxdAl9C_UxRqc2lWZNABDRNt1kPNo",
  authDomain: "fractionball-lms.firebaseapp.com",
  projectId: "fractionball-lms",
  storageBucket: "fractionball-lms.firebasestorage.app",
  messagingSenderId: "110595744029",
  appId: "1:110595744029:web:c66d6c0cdc0df3cf33c1f4",
  measurementId: "G-LXELEY5CP8"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase Authentication and get a reference to the service
export const auth = getAuth(app);

// Initialize Firebase Storage and get a reference to the service
export const storage = getStorage(app);

// Initialize Analytics (optional)
export const analytics = typeof window !== 'undefined' ? getAnalytics(app) : null;

// Connect to emulators in development (optional)
if (process.env.NODE_ENV === 'development' && typeof window !== 'undefined') {
  // Uncomment these lines if you want to use Firebase emulators locally
  // connectAuthEmulator(auth, "http://localhost:9099");
  // connectStorageEmulator(storage, "localhost", 9199);
}

export default app;
