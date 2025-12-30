import { useState, useEffect } from "react";
import { initializeApp, FirebaseApp } from "firebase/app";
import { getAuth, signInWithPopup, GoogleAuthProvider, signOut, onAuthStateChanged, User } from "firebase/auth";
import { getFirestore, collection, getDocs } from "firebase/firestore";

import { firebaseConfig } from "./firebase-config";

// Initialize Firebase
let app: FirebaseApp;
let auth: ReturnType<typeof getAuth>;
let db: ReturnType<typeof getFirestore>;

try {
  app = initializeApp(firebaseConfig);
  auth = getAuth(app);
  db = getFirestore(app);
} catch (e) {
  console.error("Firebase init error:", e);
}

// Simple Admin Panel (no FireCMS - direct Firestore access)
export default function FireCMSWrapper() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("videos");
  const [items, setItems] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Auth state listener
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
      setLoading(false);
    });
    return () => unsubscribe();
  }, []);

  // Load items when tab changes
  useEffect(() => {
    if (user) {
      loadItems();
    }
  }, [activeTab, user]);

  const loadItems = async () => {
    try {
      const querySnapshot = await getDocs(collection(db, activeTab));
      const data = querySnapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
      setItems(data);
    } catch (e: any) {
      console.error("Error loading:", e);
      setError(e.message);
    }
  };

  const handleGoogleSignIn = async () => {
    try {
      const provider = new GoogleAuthProvider();
      await signInWithPopup(auth, provider);
    } catch (e: any) {
      setError(e.message);
    }
  };

  const handleSignOut = async () => {
    await signOut(auth);
  };

  // Loading state
  if (loading) {
    return (
      <div style={styles.centered}>
        <Logo />
        <p style={{ color: "#9ca3af", marginTop: 20 }}>Loading...</p>
      </div>
    );
  }

  // Login screen
  if (!user) {
    return (
      <div style={styles.loginContainer}>
        <div style={styles.loginCard}>
          <Logo />
          <h1 style={styles.title}>FractionBall Admin</h1>
          <p style={{ color: "#9ca3af", marginBottom: 30 }}>Sign in to manage content</p>
          
          <button onClick={handleGoogleSignIn} style={styles.googleButton}>
            <svg width="20" height="20" viewBox="0 0 24 24" style={{ marginRight: 10 }}>
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Sign in with Google
          </button>
          
          {error && <p style={{ color: "#ef4444", marginTop: 20 }}>{error}</p>}
        </div>
      </div>
    );
  }

  // Main admin panel
  return (
    <div style={styles.container}>
      {/* Sidebar */}
      <aside style={styles.sidebar}>
        <div style={styles.sidebarHeader}>
          <Logo size={32} />
          <span style={styles.logoText}>FractionBall</span>
        </div>
        
        <nav style={styles.nav}>
          {["videos", "resources", "activities"].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                ...styles.navItem,
                backgroundColor: activeTab === tab ? "#1f2937" : "transparent"
              }}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </nav>

        <div style={styles.userSection}>
          <img src={user.photoURL || ""} alt="" style={styles.avatar} />
          <div>
            <p style={{ color: "white", fontSize: 14 }}>{user.displayName}</p>
            <button onClick={handleSignOut} style={styles.signOutBtn}>Sign out</button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main style={styles.main}>
        <header style={styles.header}>
          <h1 style={styles.pageTitle}>{activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}</h1>
          <button style={styles.addButton}>+ Add New</button>
        </header>

        {error && (
          <div style={styles.errorBanner}>
            <p>{error}</p>
            <p style={{ fontSize: 12, marginTop: 8 }}>
              Make sure Firestore is enabled in your Firebase Console: 
              <a href="https://console.firebase.google.com/project/fractionball-lms/firestore" target="_blank" rel="noreferrer" style={{ color: "#60a5fa" }}>
                {" "}Open Firebase Console
              </a>
            </p>
          </div>
        )}

        <div style={styles.content}>
          {items.length === 0 ? (
            <div style={styles.emptyState}>
              <p>No {activeTab} yet</p>
              <p style={{ color: "#6b7280", marginTop: 8 }}>Click "Add New" to create your first {activeTab.slice(0, -1)}</p>
            </div>
          ) : (
            <div style={styles.grid}>
              {items.map(item => (
                <div key={item.id} style={styles.card}>
                  <h3 style={{ marginBottom: 8 }}>{item.title || item.name || "Untitled"}</h3>
                  <p style={{ color: "#6b7280", fontSize: 14 }}>{item.description?.substring(0, 100) || "No description"}</p>
                  <div style={styles.cardActions}>
                    <button style={styles.editBtn}>Edit</button>
                    <button style={styles.deleteBtn}>Delete</button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

// Logo component
function Logo({ size = 40 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100">
      <circle cx="50" cy="50" r="45" fill="#EF4444"/>
      <path d="M50 15 L80 50 L50 85 L20 50 Z" fill="white"/>
    </svg>
  );
}

// Styles
const styles: Record<string, React.CSSProperties> = {
  centered: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    height: "100vh",
    backgroundColor: "#111827"
  },
  loginContainer: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    minHeight: "100vh",
    backgroundColor: "#111827"
  },
  loginCard: {
    backgroundColor: "#1f2937",
    padding: 40,
    borderRadius: 16,
    textAlign: "center" as const,
    maxWidth: 400,
    width: "100%",
    margin: 20
  },
  title: {
    color: "white",
    fontSize: 24,
    marginTop: 20,
    marginBottom: 8
  },
  googleButton: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    width: "100%",
    padding: "12px 24px",
    backgroundColor: "white",
    border: "none",
    borderRadius: 8,
    fontSize: 16,
    cursor: "pointer"
  },
  container: {
    display: "flex",
    minHeight: "100vh",
    backgroundColor: "#f3f4f6"
  },
  sidebar: {
    width: 250,
    backgroundColor: "#111827",
    padding: 20,
    display: "flex",
    flexDirection: "column"
  },
  sidebarHeader: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    marginBottom: 30
  },
  logoText: {
    color: "white",
    fontSize: 18,
    fontWeight: 600
  },
  nav: {
    flex: 1
  },
  navItem: {
    display: "block",
    width: "100%",
    padding: "12px 16px",
    color: "#9ca3af",
    border: "none",
    borderRadius: 8,
    textAlign: "left" as const,
    cursor: "pointer",
    marginBottom: 4,
    fontSize: 14
  },
  userSection: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    paddingTop: 20,
    borderTop: "1px solid #374151"
  },
  avatar: {
    width: 36,
    height: 36,
    borderRadius: "50%",
    backgroundColor: "#ef4444"
  },
  signOutBtn: {
    background: "none",
    border: "none",
    color: "#ef4444",
    cursor: "pointer",
    fontSize: 12,
    padding: 0
  },
  main: {
    flex: 1,
    padding: 30
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 30
  },
  pageTitle: {
    fontSize: 28,
    fontWeight: 600,
    color: "#111827"
  },
  addButton: {
    padding: "10px 20px",
    backgroundColor: "#ef4444",
    color: "white",
    border: "none",
    borderRadius: 8,
    cursor: "pointer",
    fontWeight: 500
  },
  errorBanner: {
    backgroundColor: "#fef2f2",
    border: "1px solid #fecaca",
    borderRadius: 8,
    padding: 16,
    marginBottom: 20,
    color: "#991b1b"
  },
  content: {
    backgroundColor: "white",
    borderRadius: 12,
    padding: 20,
    minHeight: 400
  },
  emptyState: {
    textAlign: "center" as const,
    padding: 60,
    color: "#9ca3af"
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
    gap: 20
  },
  card: {
    border: "1px solid #e5e7eb",
    borderRadius: 8,
    padding: 16
  },
  cardActions: {
    display: "flex",
    gap: 8,
    marginTop: 12
  },
  editBtn: {
    padding: "6px 12px",
    backgroundColor: "#f3f4f6",
    border: "none",
    borderRadius: 4,
    cursor: "pointer"
  },
  deleteBtn: {
    padding: "6px 12px",
    backgroundColor: "#fef2f2",
    color: "#ef4444",
    border: "none",
    borderRadius: 4,
    cursor: "pointer"
  }
};
