import {
  FireCMS,
  Scaffold,
  AppBar,
  Drawer,
  NavigationRoutes,
  SideDialogs,
  SnackbarProvider,
  useBuildNavigationController,
  CircularProgressCenter,
} from "@firecms/core";
import {
  FirebaseAuthController,
  FirebaseLoginView,
  useFirebaseAuthController,
  useFirebaseStorageSource,
  useFirestoreDelegate,
  useInitialiseFirebase,
} from "@firecms/firebase";
import { CssBaseline, ThemeProvider, createTheme } from "@mui/material";
import { FirebaseApp } from "firebase/app";
import { firebaseConfig } from "./firebase-config";

// Import all collections
import { activitiesCollection } from "./collections/activities";
import { videosCollection } from "./collections/videos";
import { resourcesCollection } from "./collections/resources";
import { taxonomiesCollection } from "./collections/taxonomies";
import { pagesCollection } from "./collections/pages";
import { menuItemsCollection } from "./collections/menuItems";
import { faqsCollection } from "./collections/faqs";
import { communityPostsCollection } from "./collections/communityPosts";
import { usersCollection } from "./collections/users";

// Create custom theme
const theme = createTheme({
  palette: {
    mode: "light",
    primary: {
      main: "#ef4444",
      light: "#f87171",
      dark: "#dc2626",
    },
    secondary: {
      main: "#fde047",
      light: "#fef08a",
      dark: "#facc15",
    },
    background: {
      default: "#f9fafb",
      paper: "#ffffff",
    },
  },
  typography: {
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif",
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: "none",
          borderRadius: 8,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
        },
      },
    },
  },
});

// Define all collections
const collections = [
  activitiesCollection,
  videosCollection,
  resourcesCollection,
  taxonomiesCollection,
  pagesCollection,
  menuItemsCollection,
  faqsCollection,
  communityPostsCollection,
  usersCollection,
];

// Loading component
function LoadingScreen({ message = "Loading Fraction Ball Admin..." }: { message?: string }) {
  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      minHeight: "100vh",
      background: "linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)",
    }}>
      <div style={{
        width: 50,
        height: 50,
        border: "4px solid #e5e7eb",
        borderTopColor: "#ef4444",
        borderRadius: "50%",
        animation: "spin 1s linear infinite",
      }} />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      <p style={{ marginTop: 16, color: "#374151", fontSize: 16, fontWeight: 500 }}>
        {message}
      </p>
    </div>
  );
}

// Error component
function ErrorScreen({ error }: { error: string }) {
  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      minHeight: "100vh",
      padding: 24,
      textAlign: "center",
      background: "#fef2f2",
    }}>
      <h2 style={{ color: "#ef4444", marginBottom: 16 }}>Configuration Error</h2>
      <p style={{ color: "#374151", maxWidth: 400 }}>{error}</p>
      <button 
        onClick={() => window.location.reload()}
        style={{
          marginTop: 24,
          padding: "12px 24px",
          background: "#ef4444",
          color: "white",
          border: "none",
          borderRadius: 8,
          cursor: "pointer",
          fontWeight: 500,
        }}
      >
        Retry
      </button>
    </div>
  );
}

// Inner app component - only rendered when Firebase is ready
function FireCMSApp({ firebaseApp }: { firebaseApp: FirebaseApp }) {
  // Firestore delegate for data operations
  const firestoreDelegate = useFirestoreDelegate({ firebaseApp });

  // Firebase storage for file uploads
  const storageSource = useFirebaseStorageSource({ firebaseApp });

  // Authentication controller
  const authController: FirebaseAuthController = useFirebaseAuthController({
    firebaseApp,
  });

  // Navigation controller
  const navigationController = useBuildNavigationController({
    collections,
    authController,
    dataSourceDelegate: firestoreDelegate,
  });

  // Check if user is authenticated
  const canAccessMainView = authController.user !== null;

  return (
    <FireCMS
      navigationController={navigationController}
      authController={authController}
      dataSourceDelegate={firestoreDelegate}
      storageSource={storageSource}
    >
      {({ loading }) => {
        if (loading) {
          return <CircularProgressCenter />;
        }

        if (!canAccessMainView) {
          return (
            <FirebaseLoginView
              allowSkipLogin={false}
              signInOptions={["google.com", "password"]}
              firebaseApp={firebaseApp}
              authController={authController}
              logo="/logo.svg"
            />
          );
        }

        return (
          <Scaffold
            autoOpenDrawer={true}
            logo="/logo.svg"
          >
            <AppBar title="Fraction Ball Admin" />
            <Drawer />
            <NavigationRoutes />
            <SideDialogs />
          </Scaffold>
        );
      }}
    </FireCMS>
  );
}

// Main App component
export default function App() {
  // Initialize Firebase first
  const { firebaseApp, firebaseConfigLoading, configError } = useInitialiseFirebase({
    firebaseConfig,
  });

  // Show loading while Firebase initializes
  if (firebaseConfigLoading) {
    return <LoadingScreen message="Initializing Firebase..." />;
  }

  // Show error if Firebase config failed
  if (configError) {
    return <ErrorScreen error={configError} />;
  }

  // Show error if no Firebase app
  if (!firebaseApp) {
    return <ErrorScreen error="Failed to initialize Firebase. Please check your configuration." />;
  }

  // Render the main app with Firebase ready
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <SnackbarProvider>
        <FireCMSApp firebaseApp={firebaseApp} />
      </SnackbarProvider>
    </ThemeProvider>
  );
}
