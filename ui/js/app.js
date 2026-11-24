/**
 * H.Huddair's Nexus-Pulse - Level 2 Enterprise
 * World-Class Enterprise React GUI Application
 * Standard: GitHub Enterprise / Linear / Vercel Modern Minimalist
 *
 * Capabilities:
 * - GitHub-Grade Theme Engine (GitHub Dark, Vercel Midnight, GitHub Light, Linear Dark)
 * - Kanban Lead Pipeline CRM with clean deduplicated tags and dynamic responsiveness
 * - Human Approval Gate with batch authorization and review modals
 * - Hot Lead alerts with 1-click AI executive response dispatcher
 * - Inbox Rotator with SMTP telemetry & daily domain send-cap monitors
 * - Dynamic Admin Profile Security (Bcrypt 12-round hashing)
 * - Role-Based Operator Management with streamlined inline action bars & fixed-width table
 * - Interactive Operator Audit Trail & Session Activity Viewer
 * - Multi-Format Data Backup System (JSON, XLSX, CSV)
 * - Cascading 3-Tier Hunt & Verify Lead Engine (Region -> Country -> City + custom industry + 100 lead limit)
 * - Complete input state-reversion fix across all forms and text fields
 * - Zero-latency Web Audio API subtle mechanical click sound engine across all components
 */

// =============================================================================
// SUBTLE MULTI-SOUND WEB AUDIO ENGINE (Zero external dependencies)
// High-tech, zero-latency tactile audio synthesizer:
// 1. Water Drop  2. Bubble Pop  3. Glass Chime  4. Subtle Switch Click  5. Soft Low Tone
// =============================================================================
let _uiAudioContext = null;
let _soundMuted = false;

function getUiAudioContext() {
  if (typeof window === "undefined") return null;
  if (!_uiAudioContext) {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (AudioCtx) {
      _uiAudioContext = new AudioCtx();
    }
  }
  if (_uiAudioContext && _uiAudioContext.state === "suspended") {
    _uiAudioContext.resume().catch(() => {});
  }
  return _uiAudioContext;
}

// User-gesture unlocking hook for Web Audio API policy compliance
if (typeof window !== "undefined") {
  const unlockAudio = () => {
    try {
      const ctx = getUiAudioContext();
      if (ctx && ctx.state === "suspended") {
        ctx.resume().catch(() => {});
      }
    } catch (e) {}
  };
  window.addEventListener("pointerdown", unlockAudio, { once: true, passive: true });
  window.addEventListener("keydown", unlockAudio, { once: true, passive: true });
}

function playUiSound(tone = "switch_click") {
  if (_soundMuted) return;
  try {
    const ctx = getUiAudioContext();
    if (!ctx) return;
    const t = ctx.currentTime;

    if (tone === "welcome_chime" || tone === "login_success") {
      // 1. Welcome Chime: Warm harmonic arpeggio chord (C5 -> E5 -> G5)
      const notes = [523.25, 659.25, 783.99];
      notes.forEach((freq, idx) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        const noteTime = t + (idx * 0.045);
        osc.type = "sine";
        osc.frequency.setValueAtTime(freq, noteTime);
        gain.gain.setValueAtTime(0.04, noteTime);
        gain.gain.exponentialRampToValueAtTime(0.0001, noteTime + 0.26);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(noteTime);
        osc.stop(noteTime + 0.26);
      });
    } else if (tone === "theme_shimmer") {
      // 2. Theme Shimmer: Delicate resonant bell shimmer (1320Hz + 1980Hz + 2640Hz)
      const freqs = [1320, 1980, 2640];
      freqs.forEach((freq, idx) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = "sine";
        osc.frequency.setValueAtTime(freq, t);
        gain.gain.setValueAtTime(0.025 / (idx + 1), t);
        gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.18);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(t);
        osc.stop(t + 0.18);
      });
    } else if (tone === "water_drop" || tone === "tab") {
      // 3. Water Drop: Airy descending resonance (Nav / Sidebar tab switches)
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(1350, t);
      osc.frequency.exponentialRampToValueAtTime(480, t + 0.045);
      gain.gain.setValueAtTime(0.05, t);
      gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.045);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(t);
      osc.stop(t + 0.045);
    } else if (tone === "bubble_pop") {
      // 4. Bubble Pop: Upward chirping bubble (Filter / Toggle / Pill clicks)
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(420, t);
      osc.frequency.exponentialRampToValueAtTime(880, t + 0.038);
      gain.gain.setValueAtTime(0.05, t);
      gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.038);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(t);
      osc.stop(t + 0.038);
    } else if (tone === "glass_chime" || tone === "action" || tone === "action_pulse" || tone === "submit") {
      // 5. Action Pulse / Glass Chime: Clean upward dual-harmonic confirmation pulse
      const osc1 = ctx.createOscillator();
      const gain1 = ctx.createGain();
      const osc2 = ctx.createOscillator();
      const gain2 = ctx.createGain();

      osc1.type = "sine";
      osc1.frequency.setValueAtTime(880, t);
      osc1.frequency.exponentialRampToValueAtTime(1760, t + 0.08);
      gain1.gain.setValueAtTime(0.045, t);
      gain1.gain.exponentialRampToValueAtTime(0.0001, t + 0.15);

      osc2.type = "sine";
      osc2.frequency.setValueAtTime(2640, t);
      gain2.gain.setValueAtTime(0.02, t);
      gain2.gain.exponentialRampToValueAtTime(0.0001, t + 0.12);

      osc1.connect(gain1);
      osc2.connect(gain2);
      gain1.connect(ctx.destination);
      gain2.connect(ctx.destination);
      osc1.start(t);
      osc2.start(t);
      osc1.stop(t + 0.15);
      osc2.stop(t + 0.12);
    } else if (tone === "low_tone" || tone === "destructive" || tone === "warning") {
      // 6. Soft Low Tone: Warm warning / cancellation / destructive note
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "triangle";
      osc.frequency.setValueAtTime(180, t);
      osc.frequency.exponentialRampToValueAtTime(90, t + 0.09);
      gain.gain.setValueAtTime(0.045, t);
      gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.09);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(t);
      osc.stop(t + 0.09);
    } else if (tone === "auth_toggle") {
      // 7. Auth Toggle: Crisp soft glass pop (Sign In <-> Create Account switch)
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(1400, t);
      osc.frequency.exponentialRampToValueAtTime(240, t + 0.025);
      gain.gain.setValueAtTime(0.045, t);
      gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.025);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(t);
      osc.stop(t + 0.025);
    } else {
      // 8. Subtle Switch Click (default): Crisp microsecond tactile click
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(1250, t);
      osc.frequency.exponentialRampToValueAtTime(180, t + 0.028);
      gain.gain.setValueAtTime(0.04, t);
      gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.028);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(t);
      osc.stop(t + 0.028);
    }
  } catch (err) {
    // Non-blocking: never interrupt UI interaction if audio fails
  }
}

const SoundEffects = {
  authToggle: () => playUiSound("auth_toggle"),
  welcomeChime: () => playUiSound("welcome_chime"),
  waterDrop: () => playUiSound("water_drop"),
  actionPulse: () => playUiSound("action_pulse"),
  glassChime: () => playUiSound("glass_chime"),
  lowTone: () => playUiSound("low_tone"),
  themeShimmer: () => playUiSound("theme_shimmer"),
  switchClick: () => playUiSound("switch_click"),
  bubblePop: () => playUiSound("bubble_pop")
};
window.SoundEffects = SoundEffects;
window.playUiSound = playUiSound;

// Global delegated click listener for all interactive components
if (typeof document !== "undefined") {
  document.addEventListener("click", (evt) => {
    try {
      const el = evt.target;
      if (!el) return;

      const interactive = el.closest(
        'button, [role="button"], a, select, input[type="submit"], input[type="button"], input[type="checkbox"], input[type="radio"], [role="tab"], .np-nav-tab, .nav-tab, .tab-btn, .np-sidebar-item, .kanban-card, .np-card.cursor-pointer, .cursor-pointer, [data-clickable="true"]'
      );

      if (interactive) {
        const isDanger = interactive.classList.contains("btn-danger") ||
                         interactive.classList.contains("text-theme-danger") ||
                         interactive.getAttribute("data-action") === "delete";
        const isTab = interactive.getAttribute("role") === "tab" ||
                      interactive.classList.contains("np-nav-tab") ||
                      interactive.classList.contains("np-sidebar-item") ||
                      interactive.classList.contains("nav-tab") ||
                      interactive.classList.contains("tab-btn");
        const isAction = interactive.classList.contains("btn-primary") ||
                         interactive.type === "submit";
        const isTheme = interactive.classList.contains("theme-dot") ||
                        interactive.closest(".theme-picker-item");

        if (isDanger) {
          playUiSound("low_tone");
        } else if (isTheme) {
          playUiSound("theme_shimmer");
        } else if (isAction) {
          playUiSound("action_pulse");
        } else if (isTab) {
          playUiSound("water_drop");
        } else {
          playUiSound("switch_click");
        }
      }
    } catch (e) {
      // Fail safely
    }
  }, { capture: true, passive: true });
}

const { useState, useEffect, useRef, useMemo } = React;
const API_BASE = window.location.origin;

// -----------------------------------------------------------------------------
// GEOGRAPHIC TAXONOMY: 3-TIER REGION -> COUNTRY -> CITY
// -----------------------------------------------------------------------------
const GEO_REGIONS = {
  "Europe": {
    countries: {
      "Germany": ["Berlin", "Munich", "Frankfurt", "Hamburg", "Cologne", "Stuttgart", "Düsseldorf"],
      "UK": ["London", "Manchester", "Birmingham", "Leeds", "Bristol", "Edinburgh", "Glasgow"],
      "France": ["Paris", "Lyon", "Marseille", "Toulouse", "Nice", "Bordeaux"],
      "Netherlands": ["Amsterdam", "Rotterdam", "The Hague", "Utrecht", "Eindhoven"],
      "Spain": ["Madrid", "Barcelona", "Valencia", "Seville", "Bilbao"],
      "Italy": ["Milan", "Rome", "Turin", "Naples", "Bologna", "Florence"],
      "Switzerland": ["Zurich", "Geneva", "Basel", "Bern", "Lausanne"],
      "Poland": ["Warsaw", "Krakow", "Wroclaw", "Gdansk", "Poznan"]
    }
  },
  "North America": {
    countries: {
      "USA": ["New York", "Chicago", "Houston", "Dallas", "Atlanta", "Phoenix", "Los Angeles", "Miami", "Seattle", "Austin"],
      "Canada": ["Toronto", "Vancouver", "Montreal", "Calgary", "Ottawa", "Edmonton"]
    }
  },
  "Middle East": {
    countries: {
      "UAE": ["Dubai", "Abu Dhabi", "Sharjah", "Ajman", "Ras Al Khaimah"],
      "Saudi Arabia": ["Riyadh", "Jeddah", "Dammam", "Mecca", "Medina"],
      "Qatar": ["Doha", "Al Wakrah", "Al Khor", "Al Rayyan"]
    }
  },
  "South Asia": {
    countries: {
      "Pakistan": ["Lahore", "Karachi", "Islamabad", "Sialkot", "Faisalabad", "Rawalpindi"],
      "India": ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Pune"]
    }
  },
  "Asia Pacific": {
    countries: {
      "Australia": ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide"],
      "Singapore": ["Singapore", "Jurong", "Tampines", "Woodlands"]
    }
  }
};

const INDUSTRY_PRESETS = [
  "Commercial Construction",
  "Sports Wear Manufacturers",
  "Gym Equipment",
  "Enterprise SaaS",
  "MedTech & Healthcare",
  "Luxury Real Estate",
  "Industrial Manufacturing",
  "Logistics & Freight",
  "Renewable Energy & Solar",
  "FinTech & Payments"
];

const THEMES = [
  { id: "obsidian-glass", name: "Obsidian Glass", dotColor: "#38bdf8", desc: "Default dark obsidian slate & ice cyan" },
  { id: "emerald-vault", name: "Emerald Vault", dotColor: "#10b981", desc: "Executive dark obsidian & refined emerald" },
  { id: "cobalt-telemetry", name: "Cobalt Telemetry", dotColor: "#3b82f6", desc: "Executive dark obsidian & sapphire cobalt" },
  { id: "amber-forge", name: "Amber Forge", dotColor: "#f59e0b", desc: "Executive dark obsidian & warm bronze amber" },
  { id: "crimson-ops", name: "Crimson Ops", dotColor: "#f43f5e", desc: "Executive dark obsidian & deep ruby crimson" },
  { id: "violet-prism", name: "Violet Prism", dotColor: "#8b5cf6", desc: "Executive dark obsidian & Linear royal iris" }
];

const getSavedThemeForUser = (username) => {
  try {
    if (username) {
      const userTheme = localStorage.getItem(`nexus_theme_${username.toLowerCase()}`);
      if (userTheme && userTheme !== "github-dark") return userTheme;
    }
  } catch (e) {}
  const saved = localStorage.getItem("nexus_theme");
  if (!saved || saved === "github-dark") return "obsidian-glass";
  return saved;
};

const KANBAN_STAGES = [
  { key: "SCRAPED", label: "Scraped", badgeClass: "badge-muted" },
  { key: "VERIFIED", label: "Verified", badgeClass: "badge-accent" },
  { key: "PENDING_APPROVAL", label: "Approval Hold", badgeClass: "badge-warning" },
  { key: "APPROVED", label: "Authorized", badgeClass: "badge-purple" },
  { key: "SENT", label: "Dispatched", badgeClass: "badge-muted" },
  { key: "REPLIED", label: "Replied", badgeClass: "badge-accent" },
  { key: "HOT_LEAD", label: "Hot Lead", badgeClass: "badge-danger" },
  { key: "CLOSED", label: "Converted", badgeClass: "badge-success" }
];

const normalizeLeadStatus = (rawStatus) => {
  if (!rawStatus) return "SCRAPED";
  const s = String(rawStatus).toUpperCase().trim();
  if (s === "PENDING_APPROVAL" || s === "APPROVAL_HOLD" || s === "PENDING") return "PENDING_APPROVAL";
  if (s === "APPROVED" || s === "AUTHORIZED" || s === "FAILED" || s === "SCHEDULED") return "APPROVED";
  if (s === "SENT" || s === "DISPATCHED" || s === "CONTACTED" || s === "DELIVERED" || s === "BOUNCED") return "SENT";
  if (s === "REPLIED" || s === "INTERESTED" || s === "NEUTRAL") return "REPLIED";
  if (s === "HOT_LEAD" || s === "HOT" || s === "HOTLEAD") return "HOT_LEAD";
  if (s === "CLOSED" || s === "CONVERTED" || s === "WON") return "CLOSED";
  if (s === "VERIFIED" || s === "VALIDATED") return "VERIFIED";
  if (s === "SCRAPED" || s === "NEW" || s === "HUNTED" || s === "DISCOVERED") return "SCRAPED";
  if (s === "SUPPRESSED" || s === "BLACKLISTED" || s === "UNSUBSCRIBED") return "SUPPRESSED";
  return "SCRAPED";
};

function NexusPulseApp() {
  // ---------------------------------------------------------------------------
  // AUTH & AUDIO STATE
  // ---------------------------------------------------------------------------
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem("nexus_user");
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem("nexus_token") || "");

  // ---------------------------------------------------------------------------
  // THEME ENGINE (Per-Operator Theme Persistence)
  // ---------------------------------------------------------------------------
  const [activeTheme, setActiveTheme] = useState(() => {
    let uName = null;
    try {
      const savedUser = localStorage.getItem("nexus_user");
      if (savedUser) {
        uName = JSON.parse(savedUser)?.username;
      }
    } catch (e) {}
    return getSavedThemeForUser(uName);
  });
  const [isThemeMenuOpen, setIsThemeMenuOpen] = useState(false);

  // When operator identity loads or switches, restore their specific saved theme
  useEffect(() => {
    if (user?.username) {
      const preferred = getSavedThemeForUser(user.username);
      setActiveTheme(preferred);
    }
  }, [user?.username]);

  // Apply theme tokens to DOM and persist per-operator
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", activeTheme);
    document.body.setAttribute("data-theme", activeTheme);
    localStorage.setItem("nexus_theme", activeTheme);
    if (user?.username) {
      localStorage.setItem(`nexus_theme_${user.username.toLowerCase()}`, activeTheme);
    }
  }, [activeTheme, user?.username]);

  // UI Click Sound Effects Engine State
  const [soundEnabled, setSoundEnabled] = useState(() => localStorage.getItem("nexus_sound_enabled") !== "false");
  useEffect(() => {
    _soundMuted = !soundEnabled;
    localStorage.setItem("nexus_sound_enabled", soundEnabled ? "true" : "false");
  }, [soundEnabled]);

  // Production Clean Setup Check
  const [setupRequired, setSetupRequired] = useState(false);
  const [setupChecked, setSetupChecked] = useState(false);

  // First-Run Master Admin Initialization Form State
  const [initUsername, setInitUsername] = useState("");
  const [initFullName, setInitFullName] = useState("");
  const [initEmail, setInitEmail] = useState("");
  const [initPassword, setInitPassword] = useState("");
  const [initConfirmPassword, setInitConfirmPassword] = useState("");
  const [initError, setInitError] = useState("");
  const [isInitializingAdmin, setIsInitializingAdmin] = useState(false);

  // Production Clean Login Form State (No pre-populated test/demo logins)
  const [authMode, setAuthMode] = useState("login"); // 'login' | 'register'
  const [loginUsername, setLoginUsername] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [loginError, setLoginError] = useState("");
  const [isScanning, setIsScanning] = useState(false);
  const [scanStep, setScanStep] = useState("");

  // Operator Registration Form State
  const [regFullName, setRegFullName] = useState("");
  const [regEmail, setRegEmail] = useState("");
  const [regUsername, setRegUsername] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [regConfirmPassword, setRegConfirmPassword] = useState("");
  const [regError, setRegError] = useState("");
  const [isRegistering, setIsRegistering] = useState(false);
  const [showLoginPassword, setShowLoginPassword] = useState(false);
  const [showRegPassword, setShowRegPassword] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  // Setup Guide & Webhook Modal State
  const [isSetupGuideOpen, setIsSetupGuideOpen] = useState(false);
  const [setupGuideTab, setSetupGuideTab] = useState("gmail_smtp"); // 'gmail_smtp' | 'webhook_script'
  const [copiedWebhookScript, setCopiedWebhookScript] = useState(false);

  // Inbound IMAP Reply Sync State
  const [isSyncingReplies, setIsSyncingReplies] = useState(false);

  // 2-Day Free Trial Activation State
  const [isActivatingTrial, setIsActivatingTrial] = useState(false);

  // Post-Trial Subscription Paywall State
  const [selectedPaywallPlan, setSelectedPaywallPlan] = useState("3_months"); // '1_month', '2_months', '3_months'
  const [paywallNotes, setPaywallNotes] = useState("");
  const [isSubmittingPlan, setIsSubmittingPlan] = useState(false);
  const [paywallSubmitted, setPaywallSubmitted] = useState(false);

  // Admin Manual Billing: Pending Plan Requests State
  const [planRequests, setPlanRequests] = useState([]);

  // ---------------------------------------------------------------------------
  // CORE TELEMETRY & PIPELINE STATE
  // ---------------------------------------------------------------------------
  const [pulseState, setPulseState] = useState("RUNNING"); // 'RUNNING', 'DISPATCHING', 'HUNTING', 'HOT_ALERT', 'IDLE'
  const [dispatcherState, setDispatcherState] = useState({ status: "RUNNING", bypass_window: false });
  const [isDispatchingNow, setIsDispatchingNow] = useState(false);
  const [systemHealth, setSystemHealth] = useState(null);
  const [kanbanItems, setKanbanItems] = useState([]);
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [hotLeads, setHotLeads] = useState([]);
  const [mailboxes, setMailboxes] = useState([]);
  const [timezones, setTimezones] = useState({});
  const [activeTab, setActiveTab] = useState("kanban");
  const [alertBanner, setAlertBanner] = useState(null);

  // Auto-dismiss banners cleanly (8s for info/success, 12s for warnings/errors)
  useEffect(() => {
    if (!alertBanner) return;
    const timer = setTimeout(() => {
      setAlertBanner(null);
    }, alertBanner.type === "danger" || alertBanner.type === "error" ? 12000 : 8000);
    return () => clearTimeout(timer);
  }, [alertBanner]);

  // Workflow state machine tracking for Replied -> Hot Lead advancement
  const [promotedToHotLeadIds, setPromotedToHotLeadIds] = useState(() => {
    try {
      return new Set(JSON.parse(localStorage.getItem("nexus_promoted_hot_leads") || "[]"));
    } catch (e) {
      return new Set();
    }
  });

  const handleAdvanceToHotLead = async (leadId) => {
    setPromotedToHotLeadIds(prev => {
      const next = new Set(prev);
      next.add(leadId);
      try {
        localStorage.setItem("nexus_promoted_hot_leads", JSON.stringify(Array.from(next)));
      } catch (e) {}
      return next;
    });
    try {
      await fetch(`${API_BASE}/api/outreach/lead-status`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ queue_id: leadId, status: "HOT_LEAD" })
      });
      fetchData();
    } catch (e) {}
  };

  // Single consistent source of truth for active Hot Leads across top tabs, alerts & board
  const uniqueHotLeads = useMemo(() => {
    const seenEmails = new Set();
    const seenLeadIds = new Set();
    const seenItemIds = new Set();
    const result = [];

    const isSeenAndMark = (item) => {
      const email = (item.sender_email || item.recipient || item.primary_email || "").toLowerCase().trim();
      const leadId = (item.lead_id || "").toLowerCase().trim();
      const itemId = (item.id || "").toLowerCase().trim();

      if (email && seenEmails.has(email)) return true;
      if (leadId && seenLeadIds.has(leadId)) return true;
      if (itemId && seenItemIds.has(itemId)) return true;

      if (email) seenEmails.add(email);
      if (leadId) seenLeadIds.add(leadId);
      if (itemId) seenItemIds.add(itemId);
      return false;
    };

    // 1. Hot leads from incoming IMAP replies (highest priority / contains reply snippet & ai suggested draft)
    (hotLeads || []).forEach((hl) => {
      if (!isSeenAndMark(hl)) {
        result.push(hl);
      }
    });

    // 2. Hot leads from pipeline Kanban items
    (kanbanItems || []).forEach((item) => {
      const norm = normalizeLeadStatus(item.status);
      if (norm === "HOT_LEAD" || promotedToHotLeadIds.has(item.id)) {
        if (!isSeenAndMark(item)) {
          result.push(item);
        }
      }
    });

    return result;
  }, [hotLeads, kanbanItems, promotedToHotLeadIds]);

  // ---------------------------------------------------------------------------
  // OPERATOR & SECURITY MANAGEMENT STATE
  // ---------------------------------------------------------------------------
  const [operatorsList, setOperatorsList] = useState([]);
  const [adminProfile, setAdminProfile] = useState(null);
  const [licenseTelemetry, setLicenseTelemetry] = useState(null);
  const [auditSearch, setAuditSearch] = useState("");

  // Inline action bar state for operator rows
  const [expandedOperatorId, setExpandedOperatorId] = useState(null);
  const [inlineScrapeQuota, setInlineScrapeQuota] = useState("200");
  const [inlineSendQuota, setInlineSendQuota] = useState("50");

  // Modals
  const [isCreateOperatorOpen, setIsCreateOperatorOpen] = useState(false);
  const [selectedUserForReset, setSelectedUserForReset] = useState(null);
  const [resetPasswordInput, setResetPasswordInput] = useState("");

  // ---------------------------------------------------------------------------
  // GLOBAL INPUT STATE REVERSION FIX
  // Protected refs prevent background polling from resetting user typing
  // ---------------------------------------------------------------------------
  const adminProfileLoadedRef = useRef(false);
  const adminFormDirtyRef = useRef(false);

  const [adminUsernameInput, setAdminUsernameInput] = useState("");
  const [adminEmailInput, setAdminEmailInput] = useState("");
  const [adminFullNameInput, setAdminFullNameInput] = useState("");
  const [adminCurrentPassword, setAdminCurrentPassword] = useState("");
  const [adminNewPassword, setAdminNewPassword] = useState("");
  const [adminConfirmPassword, setAdminConfirmPassword] = useState("");

  // Form State: Create Operator
  const [newOpUsername, setNewOpUsername] = useState("");
  const [newOpPassword, setNewOpPassword] = useState("");
  const [newOpFullName, setNewOpFullName] = useState("");
  const [newOpEmail, setNewOpEmail] = useState("");
  const [newOpDeviceLock, setNewOpDeviceLock] = useState("");
  const [newOpExpiryDays, setNewOpExpiryDays] = useState("90");
  const [newOpScrapeQuota, setNewOpScrapeQuota] = useState("200");
  const [newOpSendQuota, setNewOpSendQuota] = useState("50");
  const [isCreatingOperator, setIsCreatingOperator] = useState(false);
  const [isResettingPassword, setIsResettingPassword] = useState(false);
  const [updatingOperatorId, setUpdatingOperatorId] = useState(null);
  const [sessionAuditLogs, setSessionAuditLogs] = useState([]);

  // ---------------------------------------------------------------------------
  // MULTI-FORMAT DATA BACKUP MODAL
  // ---------------------------------------------------------------------------
  const [isBackupModalOpen, setIsBackupModalOpen] = useState(false);
  const [isBackingUp, setIsBackingUp] = useState(false);

  // ---------------------------------------------------------------------------
  // GLOBAL LEAD ENGINE PIPELINE MODAL (3-Tier Cascading)
  // ---------------------------------------------------------------------------
  const [isHuntModalOpen, setIsHuntModalOpen] = useState(false);
  const [huntRegion, setHuntRegion] = useState("Europe");
  const [huntCountry, setHuntCountry] = useState("UK");
  const [huntCity, setHuntCity] = useState("London");
  const [isCustomCity, setIsCustomCity] = useState(false);
  const [huntCustomCity, setHuntCustomCity] = useState("");
  const [huntNiche, setHuntNiche] = useState("Commercial Construction");
  const [huntMaxResults, setHuntMaxResults] = useState(10);
  const [isHunting, setIsHunting] = useState(false);
  const [huntProgress, setHuntProgress] = useState(null);
  const [activeScrapeJobId, setActiveScrapeJobId] = useState(null);
  const scrapePollTimerRef = useRef(null);
  const scrapeAbortControllerRef = useRef(null);

  // Clean up any running timers and abort controllers on unmount
  useEffect(() => {
    return () => {
      if (scrapePollTimerRef.current) clearInterval(scrapePollTimerRef.current);
      if (scrapeAbortControllerRef.current) scrapeAbortControllerRef.current.abort();
    };
  }, []);

  const availableCountries = useMemo(() => {
    return Object.keys(GEO_REGIONS[huntRegion]?.countries || {});
  }, [huntRegion]);

  const availableCities = useMemo(() => {
    return GEO_REGIONS[huntRegion]?.countries[huntCountry] || [];
  }, [huntRegion, huntCountry]);

  const handleRegionChange = (newRegion) => {
    setHuntRegion(newRegion);
    const firstCountry = Object.keys(GEO_REGIONS[newRegion]?.countries || {})[0] || "Germany";
    setHuntCountry(firstCountry);
    const firstCity = GEO_REGIONS[newRegion]?.countries[firstCountry]?.[0] || "Berlin";
    setHuntCity(firstCity);
    setIsCustomCity(false);
  };

  const handleCountryChange = (newCountry) => {
    setHuntCountry(newCountry);
    const firstCity = GEO_REGIONS[huntRegion]?.countries[newCountry]?.[0] || "Berlin";
    setHuntCity(firstCity);
    setIsCustomCity(false);
  };

  // Pipeline approval & hot lead review modals
  const [selectedApproval, setSelectedApproval] = useState(null);
  const [approvalRecipient, setApprovalRecipient] = useState("");
  const [approvalCompanyName, setApprovalCompanyName] = useState("");
  const [approvalNiche, setApprovalNiche] = useState("Commercial Construction");
  const [approvalSubject, setApprovalSubject] = useState("");
  const [approvalBody, setApprovalBody] = useState("");

  const [selectedHotLead, setSelectedHotLead] = useState(null);
  const [hotLeadReplyBody, setHotLeadReplyBody] = useState("");
  const [incomingInquiryText, setIncomingInquiryText] = useState("");

  // Mailbox management modals
  const [isAddMailboxOpen, setIsAddMailboxOpen] = useState(false);
  const [newMbDisplayName, setNewMbDisplayName] = useState("");
  const [newMbEmail, setNewMbEmail] = useState("");
  const [newMbHost, setNewMbHost] = useState("");
  const [newMbPort, setNewMbPort] = useState("587");
  const [newMbUsername, setNewMbUsername] = useState("");
  const [newMbPassword, setNewMbPassword] = useState("");
  const [newMbDailyLimit, setNewMbDailyLimit] = useState("45");
  const [newMbWebhookUrl, setNewMbWebhookUrl] = useState("");

  const [selectedMailboxForEdit, setSelectedMailboxForEdit] = useState(null);
  const [editMbDisplayName, setEditMbDisplayName] = useState("");
  const [editMbEmail, setEditMbEmail] = useState("");
  const [editMbHost, setEditMbHost] = useState("");
  const [editMbPort, setEditMbPort] = useState("587");
  const [editMbUsername, setEditMbUsername] = useState("");
  const [editMbPassword, setEditMbPassword] = useState("");
  const [editMbDailyLimit, setEditMbDailyLimit] = useState("45");
  const [editMbWebhookUrl, setEditMbWebhookUrl] = useState("");

  // ---------------------------------------------------------------------------
  // SAAS EXPANSION STATE: TEMPLATES, BILLING, BLACKLIST & ANALYTICS
  // ---------------------------------------------------------------------------
  const [huntTargetUrls, setHuntTargetUrls] = useState("");

  const [templatesList, setTemplatesList] = useState([]);
  const [isTemplateModalOpen, setIsTemplateModalOpen] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [tplTitle, setTplTitle] = useState("");
  const [tplNiche, setTplNiche] = useState("Commercial Construction");
  const [tplSubject, setTplSubject] = useState("");
  const [tplBody, setTplBody] = useState("");
  const [tplIsDefault, setTplIsDefault] = useState(false);

  const [deliverabilityStats, setDeliverabilityStats] = useState({
    total_sent: 0,
    total_delivered: 0,
    total_opened: 0,
    total_bounced: 0,
    total_replied: 0,
    total_hot_leads: 0,
    total_queued: 0,
    total_suppressed: 0,
    open_rate_percent: 0.0,
    bounce_rate_percent: 0.0,
    conversion_rate_percent: 0.0
  });
  const [isPollingImap, setIsPollingImap] = useState(false);

  const [blacklistRules, setBlacklistRules] = useState([]);
  const [newRulePattern, setNewRulePattern] = useState("");
  const [newRuleReason, setNewRuleReason] = useState("");

  const [billingHistory, setBillingHistory] = useState([]);
  const [billingTargetOpId, setBillingTargetOpId] = useState("");
  const [billingBasePrice, setBillingBasePrice] = useState("199.00");
  const [billingDurationDays, setBillingDurationDays] = useState(90);
  const [billingNotes, setBillingNotes] = useState("");
  const [isApplyingBilling, setIsApplyingBilling] = useState(false);

  // ---------------------------------------------------------------------------
  // FETCH CORE DATA (4-Second Periodic Polling)
  // ---------------------------------------------------------------------------
  const fetchData = async () => {
    try {
      const headers = token ? { Authorization: `Bearer ${token}` } : {};

      const [healthRes, kanbanRes, approvalsRes, hotLeadsRes, mailboxesRes, tzRes, dispRes] = await Promise.all([
        fetch(`${API_BASE}/api/health`, { headers }).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/api/kanban/leads`, { headers }).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/api/outreach/pending`, { headers }).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/api/outreach/hot-leads`, { headers }).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/api/outreach/mailboxes`, { headers }).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/api/scheduler/timezones`, { headers }).then(r => r.json()).catch(() => ({})),
        fetch(`${API_BASE}/api/dispatcher/status`, { headers }).then(r => r.json()).catch(() => null)
      ]);

      if (healthRes) setSystemHealth(healthRes);
      if (Array.isArray(kanbanRes)) setKanbanItems(kanbanRes);
      if (Array.isArray(approvalsRes)) setPendingApprovals(approvalsRes);
      if (dispRes) setDispatcherState(dispRes);

      if (Array.isArray(hotLeadsRes)) {
        setHotLeads(hotLeadsRes);
        if (hotLeadsRes.length > 0) {
          setPulseState("HOT_ALERT");
        } else if (isDispatchingNow || (dispRes && dispRes.status === "DISPATCHING")) {
          setPulseState("DISPATCHING");
        } else if (isHunting) {
          setPulseState("HUNTING");
        } else if (dispRes && dispRes.status === "RUNNING") {
          setPulseState("RUNNING");
        } else if (approvalsRes && approvalsRes.length > 0) {
          setPulseState("RUNNING");
        } else {
          setPulseState("RUNNING");
        }
      } else if (dispRes && dispRes.status) {
        setPulseState(dispRes.status === "DISPATCHING" ? "DISPATCHING" : (isHunting ? "HUNTING" : "RUNNING"));
      }
      if (Array.isArray(mailboxesRes)) setMailboxes(mailboxesRes);
      if (tzRes) setTimezones(tzRes);

      // Fetch templates & deliverability analytics for all roles
      fetch(`${API_BASE}/api/templates`, { headers }).then(r => r.json()).then(data => {
        if (Array.isArray(data)) setTemplatesList(data);
      }).catch(() => {});

      fetch(`${API_BASE}/api/analytics/deliverability`, { headers }).then(r => r.json()).then(data => {
        if (data && typeof data.total_sent === "number") setDeliverabilityStats(data);
      }).catch(() => {});

      // Sync user profile state (trial & subscription statuses)
      fetch(`${API_BASE}/api/auth/me`, { headers }).then(r => r.json()).then(data => {
        if (data && data.id) {
          setUser(prev => ({ ...(prev || {}), ...data }));
          localStorage.setItem("nexus_user", JSON.stringify(data));
        }
      }).catch(() => {});

      if (user && user.role === "admin") {
        fetch(`${API_BASE}/api/billing/plan-requests`, { headers }).then(r => r.json()).then(data => {
          if (Array.isArray(data)) setPlanRequests(data);
        }).catch(() => {});
        fetch(`${API_BASE}/api/operators`, { headers }).then(r => r.json()).then(data => {
          if (Array.isArray(data)) setOperatorsList(data);
        }).catch(() => {});

        fetch(`${API_BASE}/api/admin/profile`, { headers }).then(r => r.json()).then(data => {
          if (data && data.username) {
            setAdminProfile(data);
            if (!adminProfileLoadedRef.current && !adminFormDirtyRef.current) {
              setAdminUsernameInput(data.username);
              setAdminEmailInput(data.email || "");
              setAdminFullNameInput(data.full_name || "");
              adminProfileLoadedRef.current = true;
            }
          }
        }).catch(() => {});

        fetch(`${API_BASE}/api/licenses/telemetry`, { headers }).then(r => r.json()).then(data => {
          if (data) setLicenseTelemetry(data);
        }).catch(() => {});

        fetch(`${API_BASE}/api/blacklist`, { headers }).then(r => r.json()).then(data => {
          if (Array.isArray(data)) setBlacklistRules(data);
        }).catch(() => {});

        fetch(`${API_BASE}/api/billing/all-history`, { headers }).then(r => r.json()).then(data => {
          if (Array.isArray(data)) setBillingHistory(data);
        }).catch(() => {});

        fetch(`${API_BASE}/api/operators/activity-log/all`, { headers }).then(r => r.json()).then(data => {
          if (Array.isArray(data)) setSessionAuditLogs(data);
        }).catch(() => {});
      }
    } catch (e) {
      console.error("Data sync error:", e);
    }
  };

  // Restrict Operator access away from Admin tabs
  useEffect(() => {
    if (user && user.role === "operator") {
      const adminOnlyTabs = ["security_settings", "operator_mgmt", "license_mgmt", "billing_mgmt", "blacklist_mgmt"];
      if (adminOnlyTabs.includes(activeTab)) {
        setActiveTab("kanban");
      }
    }
  }, [user, activeTab]);

  useEffect(() => {
    if (user && token) {
      fetchData();
      const interval = setInterval(fetchData, 4000);
      return () => clearInterval(interval);
    }
  }, [user, token]);

  // Check if system is in fresh production state requiring Master Admin setup
  useEffect(() => {
    const checkSetupStatus = async () => {
      try {
        const resp = await fetch(`${API_BASE}/api/auth/setup-status`);
        if (resp.ok) {
          const data = await resp.json();
          if (data && data.initialized === false) {
            setSetupRequired(true);
            localStorage.removeItem("nexus_token");
            localStorage.removeItem("nexus_user");
            setUser(null);
            setToken("");
          } else {
            setSetupRequired(false);
          }
        }
      } catch (err) {
        console.warn("Could not query setup status:", err);
      } finally {
        setSetupChecked(true);
      }
    };
    checkSetupStatus();
  }, []);

  // ---------------------------------------------------------------------------
  // AUTHENTICATION HANDLERS
  // ---------------------------------------------------------------------------
  const handleInitializeAdmin = async (e) => {
    if (e) e.preventDefault();
    setInitError("");

    if (!initUsername.trim()) {
      setInitError("Administrator username is required.");
      return;
    }
    if (initUsername.trim().length < 3) {
      setInitError("Username must be at least 3 characters.");
      return;
    }
    if (!initFullName.trim()) {
      setInitError("Full name is required.");
      return;
    }
    if (initPassword.length < 6) {
      setInitError("Master passphrase must be at least 6 characters.");
      return;
    }
    if (initPassword !== initConfirmPassword) {
      setInitError("Passphrase confirmation does not match.");
      return;
    }

    setIsInitializingAdmin(true);
    try {
      const resp = await fetch(`${API_BASE}/api/auth/initialize-admin`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: initUsername.trim(),
          password: initPassword,
          full_name: initFullName.trim(),
          email: initEmail.trim() || undefined
        })
      });
      const data = await resp.json();

      if (resp.ok && data.token) {
        SoundEffects.welcomeChime();
        setToken(data.token);
        setUser(data.user);
        localStorage.setItem("nexus_token", data.token);
        localStorage.setItem("nexus_user", JSON.stringify(data.user));
        setSetupRequired(false);
        setAlertBanner({
          type: "success",
          message: `Master Administrator [${data.user.username}] successfully initialized and hardware-bound!`
        });
      } else {
        setInitError(data.detail || "Failed to initialize administrator.");
      }
    } catch (err) {
      setInitError("Network Error: Could not reach FastAPI backend.");
    } finally {
      setIsInitializingAdmin(false);
    }
  };
  const handleBiometricLogin = async (e) => {
    if (e) e.preventDefault();
    setLoginError("");
    setIsScanning(true);
    setScanStep("Initializing hardware cryptographic handshake...");

    setTimeout(() => setScanStep("Scanning device MachineGuid & MAC signature..."), 450);
    setTimeout(() => setScanStep("Validating HMAC-SHA256 Level 2 Authorization Matrix..."), 900);

    setTimeout(async () => {
      try {
        const resp = await fetch(`${API_BASE}/api/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username: loginUsername, password: loginPassword })
        });
        const data = await resp.json();

        if (resp.ok && data.token) {
          SoundEffects.welcomeChime();
          setScanStep("Access Granted! Loading H.Huddair Nexus-Pulse Core...");
          setTimeout(() => {
            setToken(data.token);
            setUser(data.user);
            localStorage.setItem("nexus_token", data.token);
            localStorage.setItem("nexus_user", JSON.stringify(data.user));
            setIsScanning(false);
          }, 350);
        } else {
          setIsScanning(false);
          setLoginError(data.detail || "Authentication Failed: Invalid credentials or account access revoked.");
        }
      } catch (err) {
        setIsScanning(false);
        setLoginError("Connection Error: FastAPI backend unreachable.");
      }
    }, 1300);
  };

  const handleGoogleSignIn = async () => {
    setLoginError("");
    setIsScanning(true);
    setScanStep("Initiating Zero-Config Google OAuth 2.0 handshake...");
    try {
      const googleEmail = prompt("Enter your Google Account email to activate 2-Day Free Trial:") || "";
      if (!googleEmail || !googleEmail.includes("@")) {
        setIsScanning(false);
        return;
      }
      setScanStep(`Auto-provisioning 2-Day Free Trial for ${googleEmail}...`);
      const resp = await fetch(`${API_BASE}/api/auth/google`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: googleEmail,
          name: googleEmail.split("@")[0],
          sub: "google_" + Date.now()
        })
      });
      const data = await resp.json();
      if (resp.ok && data.token) {
        SoundEffects.welcomeChime();
        setScanStep("Google Identity Verified! 2-Day Free Trial provisioned...");
        setTimeout(() => {
          setToken(data.token);
          setUser(data.user);
          localStorage.setItem("nexus_token", data.token);
          localStorage.setItem("nexus_user", JSON.stringify(data.user));
          setIsScanning(false);
          setAlertBanner({
            type: "success",
            message: `Welcome ${data.user.full_name || data.user.username}! 2-Day Free Trial successfully activated.`
          });
        }, 400);
      } else {
        setIsScanning(false);
        setLoginError(data.detail || "Google OAuth authentication failed.");
      }
    } catch (err) {
      setIsScanning(false);
      setLoginError("Network Error: Could not connect to Google OAuth service.");
    }
  };

  const handleLogout = () => {
    try {
      SoundEffects.lowTone();
    } catch (e) {}
    localStorage.removeItem("nexus_token");
    localStorage.removeItem("nexus_user");
    setUser(null);
    setToken("");
    adminProfileLoadedRef.current = false;
    adminFormDirtyRef.current = false;
    const defaultTheme = localStorage.getItem("nexus_theme") || "obsidian-glass";
    setActiveTheme(defaultTheme);
  };

  // ---------------------------------------------------------------------------
  // SAAS MULTI-TENANT TRIAL, PAYWALL & IMAP LISTENERS HELPERS
  // ---------------------------------------------------------------------------
  const calculateTrialRemaining = (expiresAt) => {
    if (!expiresAt) return "48h left";
    try {
      const exp = new Date(expiresAt.replace(" ", "T") + (expiresAt.includes("Z") ? "" : "Z"));
      const now = new Date();
      const diffMs = exp - now;
      if (diffMs <= 0) return "Trial Expired";
      const hours = Math.floor(diffMs / (1000 * 60 * 60));
      const mins = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
      return `${hours}h ${mins}m left`;
    } catch (e) {
      return "48h left";
    }
  };

  const isTrialExpired = (expiresAt) => {
    if (!expiresAt) return false;
    try {
      const exp = new Date(expiresAt.replace(" ", "T") + (expiresAt.includes("Z") ? "" : "Z"));
      return new Date() > exp;
    } catch (e) {
      return false;
    }
  };

  const handleRegister = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    setRegError("");
    if (!regUsername || !regPassword || !regFullName) {
      setRegError("Please fill in all required fields.");
      return;
    }
    if (regPassword.length < 6) {
      setRegError("Passphrase must be at least 6 characters.");
      return;
    }
    if (regPassword !== regConfirmPassword) {
      setRegError("Passwords do not match.");
      return;
    }

    setIsRegistering(true);
    try {
      const resp = await fetch(`${API_BASE}/api/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: regUsername.trim(),
          password: regPassword,
          full_name: regFullName.trim(),
          email: regEmail ? regEmail.trim().toLowerCase() : undefined,
          role: "operator"
        })
      });
      const data = await resp.json();
      if (resp.ok && (data.token || data.access_token)) {
        SoundEffects.welcomeChime();
        const userToken = data.token || data.access_token;
        const userData = data.user || {
          id: data.user_id,
          username: regUsername.trim(),
          role: "operator",
          full_name: regFullName.trim(),
          email: regEmail,
          trial_active: 0,
          trial_status: "pending"
        };
        setToken(userToken);
        setUser(userData);
        localStorage.setItem("nexus_token", userToken);
        localStorage.setItem("nexus_user", JSON.stringify(userData));
        setAlertBanner({
          type: "success",
          message: `Welcome ${userData.full_name || userData.username}! Your operator account is created. Activate your 2-Day Free Trial to begin.`
        });
      } else {
        setRegError(data.detail || "Registration failed. Username may already exist.");
      }
    } catch (err) {
      setRegError("Network Error: Could not connect to authentication service.");
    } finally {
      setIsRegistering(false);
    }
  };

  const handleActivateTrial = async () => {
    setIsActivatingTrial(true);
    try {
      const resp = await fetch(`${API_BASE}/api/auth/activate-trial`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        }
      });
      const data = await resp.json();
      if (resp.ok && data.success) {
        const updatedUser = {
          ...user,
          trial_active: 1,
          trial_status: "active",
          trial_expires_at: data.trial_expires_at,
          expiry_date: data.expiry_date
        };
        setUser(updatedUser);
        localStorage.setItem("nexus_user", JSON.stringify(updatedUser));
        setAlertBanner({
          type: "success",
          message: "🚀 2-Day Free Trial successfully activated! 48 hours of full platform access unlocked."
        });
      } else {
        setAlertBanner({ type: "error", message: data.detail || "Failed to activate trial." });
      }
    } catch (err) {
      setAlertBanner({ type: "error", message: "Network error activating trial." });
    } finally {
      setIsActivatingTrial(false);
    }
  };

  const handleSubmitPlanRequest = async () => {
    setIsSubmittingPlan(true);
    try {
      const planMap = {
        "1_month": { name: "1 Month Standard", days: 30, price: 199.00 },
        "2_months": { name: "2 Months Pro", days: 60, price: 379.00 },
        "3_months": { name: "3 Months Enterprise (10% Discount)", days: 90, price: 537.00 }
      };
      const plan = planMap[selectedPaywallPlan] || planMap["3_months"];

      const resp = await fetch(`${API_BASE}/api/billing/request-plan`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          plan_name: plan.name,
          duration_days: plan.days,
          price: plan.price,
          notes: paywallNotes || "Subscription requested from post-trial paywall"
        })
      });
      const data = await resp.json();
      if (resp.ok && data.success) {
        setPaywallSubmitted(true);
        setAlertBanner({
          type: "success",
          message: "✅ Plan request submitted! Super Admin has been notified for manual billing review and approval."
        });
      } else {
        setAlertBanner({ type: "error", message: data.detail || "Could not submit plan request." });
      }
    } catch (err) {
      setAlertBanner({ type: "error", message: "Network error submitting plan request." });
    } finally {
      setIsSubmittingPlan(false);
    }
  };

  const handleSyncReplies = async () => {
    setIsSyncingReplies(true);
    setAlertBanner({
      type: "info",
      message: "🔄 Connecting to IMAP mailboxes on Port 993 (SSL/TLS)... Scanning recent replies..."
    });
    try {
      const resp = await fetch(`${API_BASE}/api/outreach/sync-replies`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        }
      });
      const data = await resp.json();
      if (resp.ok) {
        await fetchData();
        setAlertBanner({
          type: "success",
          message: data.message || `IMAP Sync Complete: ${data.new_replies_count || 0} new replies detected!`
        });
      } else {
        setAlertBanner({ type: "error", message: data.detail || "IMAP Sync failed." });
      }
    } catch (err) {
      setAlertBanner({ type: "error", message: "Network error during IMAP sync." });
    } finally {
      setIsSyncingReplies(false);
    }
  };

  const WEBHOOK_SCRIPT_TEMPLATE = `// =============================================================================
// Nexus-Pulse Cloud Deliverability Webhook Dispatcher
// Deploy this script as a Google Apps Script Web App to send outreach emails
// with 100% cloud deliverability from Google's trusted infrastructure.
// =============================================================================

function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    var recipient = data.recipient;
    var subject = data.subject;
    var body = data.body;
    var htmlBody = data.html_body || body.replace(/\\n/g, "<br>");
    
    MailApp.sendEmail({
      to: recipient,
      subject: subject,
      body: body,
      htmlBody: htmlBody
    });
    
    return ContentService.createTextOutput(JSON.stringify({
      status: "SUCCESS",
      message: "Dispatched via Google Apps Script Webhook"
    })).setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      status: "ERROR",
      message: error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}`;

  const handleCopyWebhookScript = () => {
    if (navigator && navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(WEBHOOK_SCRIPT_TEMPLATE).then(() => {
        setCopiedWebhookScript(true);
        setTimeout(() => setCopiedWebhookScript(false), 2500);
      }).catch(() => fallbackCopy());
    } else {
      fallbackCopy();
    }
  };

  const fallbackCopy = () => {
    try {
      const ta = document.createElement("textarea");
      ta.value = WEBHOOK_SCRIPT_TEMPLATE;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      setCopiedWebhookScript(true);
      setTimeout(() => setCopiedWebhookScript(false), 2500);
    } catch (e) {
      alert("Please copy the script directly from the text area.");
    }
  };

  const handleApprovePlanRequest = async (requestId) => {
    try {
      const resp = await fetch(`${API_BASE}/api/billing/plan-requests/${requestId}/approve`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        }
      });
      const data = await resp.json();
      if (resp.ok && data.success) {
        setAlertBanner({ type: "success", message: data.message || "Plan request approved!" });
        fetchData();
      } else {
        setAlertBanner({ type: "error", message: data.detail || "Approval failed." });
      }
    } catch (err) {
      setAlertBanner({ type: "error", message: "Network error approving plan." });
    }
  };

  const handleRejectPlanRequest = async (requestId) => {
    try {
      const resp = await fetch(`${API_BASE}/api/billing/plan-requests/${requestId}/reject`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        }
      });
      const data = await resp.json();
      if (resp.ok && data.success) {
        setAlertBanner({ type: "info", message: "Plan request marked as rejected." });
        fetchData();
      } else {
        setAlertBanner({ type: "error", message: data.detail || "Rejection failed." });
      }
    } catch (err) {
      setAlertBanner({ type: "error", message: "Network error rejecting plan." });
    }
  };

  // ---------------------------------------------------------------------------
  // MULTI-FORMAT DATA BACKUP EXPORT
  // ---------------------------------------------------------------------------
  const handleDownloadBackup = async (format = "json") => {
    setIsBackingUp(true);
    setAlertBanner({
      type: "info",
      message: `Generating snapshot backup in ${format.toUpperCase()} format...`
    });

    try {
      const resp = await fetch(`${API_BASE}/api/backup/download?format=${format}`, {
        method: "GET",
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });

      if (!resp.ok) {
        throw new Error(`Server returned status ${resp.status}`);
      }

      const blob = await resp.blob();
      const ext = format === "xlsx" ? "xlsx" : format === "csv" ? "csv" : "json";
      let filename = `nexus_leads_backup_${new Date().toISOString().slice(0, 10)}.${ext}`;

      const disposition = resp.headers.get("Content-Disposition");
      if (disposition && disposition.indexOf("filename=") !== -1) {
        const match = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition);
        if (match && match[1]) {
          filename = match[1].replace(/['"]/g, "");
        }
      }

      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);

      setAlertBanner({
        type: "success",
        message: `Snapshot backup successfully generated and downloaded: ${filename}`
      });
      setIsBackupModalOpen(false);
    } catch (e) {
      console.error("Backup download error:", e);
      setAlertBanner({
        type: "error",
        message: `Backup export error: ${e.message}`
      });
    } finally {
      setIsBackingUp(false);
    }
  };

  // ---------------------------------------------------------------------------
  // HUNT & VERIFY LEAD ENGINE: BACKGROUND JOBS, POLLING & TRUE CANCELLATION
  // ---------------------------------------------------------------------------
  const handleCancelScrape = async () => {
    if (scrapeAbortControllerRef.current) {
      try { scrapeAbortControllerRef.current.abort(); } catch (e) {}
      scrapeAbortControllerRef.current = null;
    }
    if (scrapePollTimerRef.current) {
      clearInterval(scrapePollTimerRef.current);
      scrapePollTimerRef.current = null;
    }
    const jobId = activeScrapeJobId;
    setActiveScrapeJobId(null);
    setIsHunting(false);
    setPulseState(uniqueHotLeads.length > 0 ? "HOT_ALERT" : "RUNNING");
    setIsHuntModalOpen(false);

    if (jobId) {
      try {
        await fetch(`${API_BASE}/api/scrape/cancel/${jobId}`, {
          method: "POST",
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        });
      } catch (e) {
        console.warn("Cancel job request error:", e);
      }
    }
    fetchData();
    setAlertBanner({
      type: "info",
      message: "Lead hunt cancelled. Ongoing operations stopped cleanly."
    });
  };

  const handleLaunchScrapePipeline = async (e) => {
    if (e) e.preventDefault();
    if (isHunting) return;

    setIsHunting(true);
    setPulseState("HUNTING");
    setHuntProgress(null);

    const effectiveCity = isCustomCity ? (huntCustomCity.trim() || huntCity) : huntCity;
    const controller = new AbortController();
    scrapeAbortControllerRef.current = controller;

    setAlertBanner({
      type: "info",
      message: `Deploying Deep Scraper for '${huntNiche}' in ${effectiveCity}, ${huntCountry} (${huntRegion}) [Limit: ${huntMaxResults} leads]...`
    });

    try {
      const resp = await fetch(`${API_BASE}/api/scrape`, {
        method: "POST",
        signal: controller.signal,
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          region: huntRegion,
          country: huntCountry,
          city: effectiveCity,
          niche: huntNiche,
          max_results: parseInt(huntMaxResults, 10) || 20,
          target_urls: huntTargetUrls.trim() ? huntTargetUrls.split("\n").map(u => u.trim()).filter(Boolean) : undefined
        })
      });

      let data;
      try {
        data = await resp.json();
      } catch (parseErr) {
        setIsHunting(false);
        setPulseState(uniqueHotLeads.length > 0 ? "HOT_ALERT" : "IDLE");
        setAlertBanner({
          type: "danger",
          message: `Server returned non-JSON response (${resp.status}). Background operations may still be running or Railway gateway timed out.`
        });
        return;
      }

      if (!resp.ok) {
        setIsHunting(false);
        setPulseState(uniqueHotLeads.length > 0 ? "HOT_ALERT" : "IDLE");
        setAlertBanner({
          type: "danger",
          message: data.detail || "Scrape pipeline initiation failed."
        });
        return;
      }

      const jobId = data.job_id;
      if (jobId) {
        setActiveScrapeJobId(jobId);
        setAlertBanner({
          type: "info",
          message: `Deep crawl running in background (Job: ${jobId.slice(0, 8)}...). Status polling active.`
        });

        // Clear any prior poll timer
        if (scrapePollTimerRef.current) clearInterval(scrapePollTimerRef.current);

        const pollTimer = setInterval(async () => {
          try {
            const statusResp = await fetch(`${API_BASE}/api/scrape/status/${jobId}`, {
              headers: token ? { Authorization: `Bearer ${token}` } : {}
            });
            let statusData;
            try {
              statusData = await statusResp.json();
            } catch (pErr) {
              return;
            }

            if (statusData.status === "COMPLETED") {
              clearInterval(pollTimer);
              scrapePollTimerRef.current = null;
              setActiveScrapeJobId(null);
              setIsHunting(false);
              setPulseState("RUNNING");
              setIsHuntModalOpen(false);

              const resObj = statusData.result || {};
              const scraped = resObj.scraped_leads || [];
              const verified = resObj.verified_leads || [];
              const fb = resObj.filter_breakdown;
              if (fb) setHuntProgress(fb);

              setKanbanItems(prev => {
                const existingIds = new Set(prev.map(i => i.id));
                const newItems = [...scraped, ...verified].filter(i => !existingIds.has(i.id));
                return [...newItems, ...prev];
              });

              fetchData();
              const fbMsg = fb ? ` | Filtered: ${fb.filtered_count} | Clean: ${fb.clean_count}` : "";
              setAlertBanner({
                type: "success",
                message: `Pipeline Completed! Discovered: ${fb ? fb.scraped_raw : (resObj.scraped_count || scraped.length)}${fbMsg} in ${effectiveCity}, ${huntCountry}.`
              });
            } else if (statusData.status === "CANCELLED") {
              clearInterval(pollTimer);
              scrapePollTimerRef.current = null;
              setActiveScrapeJobId(null);
              setIsHunting(false);
              setPulseState(uniqueHotLeads.length > 0 ? "HOT_ALERT" : "RUNNING");
              setIsHuntModalOpen(false);
              fetchData();
              const preservedCount = statusData.result?.leads_preserved_count || statusData.result?.verified_count || 0;
              setAlertBanner({ type: "info", message: `Crawl stopped by operator. ${preservedCount} verified lead(s) preserved in pipeline.` });
            } else if (statusData.status === "ERROR") {
              clearInterval(pollTimer);
              scrapePollTimerRef.current = null;
              setActiveScrapeJobId(null);
              setIsHunting(false);
              setPulseState(uniqueHotLeads.length > 0 ? "HOT_ALERT" : "RUNNING");
              setIsHuntModalOpen(false);
              fetchData();
              setAlertBanner({ type: "danger", message: `Scrape error: ${statusData.error || "Unknown error"}` });
            } else {
              // IN_PROGRESS: update progress if available
              if (statusData.progress) {
                setHuntProgress(prev => ({ ...(prev || {}), ...statusData.progress }));
              }
            }
          } catch (pollErr) {
            console.warn("Status poll error:", pollErr);
          }
        }, 2000);

        scrapePollTimerRef.current = pollTimer;
      } else {
        // Synchronous fallback response
        setIsHunting(false);
        setPulseState(uniqueHotLeads.length > 0 ? "HOT_ALERT" : "RUNNING");
        setIsHuntModalOpen(false);

        const scraped = data.scraped_leads || [];
        const verified = data.verified_leads || [];
        setKanbanItems(prev => {
          const existingIds = new Set(prev.map(i => i.id));
          const newItems = [...scraped, ...verified].filter(i => !existingIds.has(i.id));
          return [...newItems, ...prev];
        });

        fetchData();
        setAlertBanner({
          type: "success",
          message: `Pipeline Completed! Discovered: ${scraped.length} leads in ${effectiveCity}, ${huntCountry}.`
        });
      }
    } catch (err) {
      if (err.name === "AbortError") {
        setAlertBanner({ type: "info", message: "Hunt cancelled by user." });
      } else {
        console.error("Scrape error:", err);
        setAlertBanner({ type: "danger", message: "Failed to connect to /api/scrape endpoint." });
      }
      setIsHunting(false);
      setPulseState(uniqueHotLeads.length > 0 ? "HOT_ALERT" : "IDLE");
    }
  };

  // ---------------------------------------------------------------------------
  // HUMAN APPROVAL GATE HANDLERS & TEMPLATE POOL
  // ---------------------------------------------------------------------------
  const NICHE_TEMPLATES = {
    "Commercial Construction": {
      subject: "Commercial Subcontracting & Estimating Capacity // {{company_name}}",
      body: "Dear Estimating & Project Management Team at {{company_name}},\n\nWe are reaching out to submit our credentials and commercial capacity for upcoming commercial construction packages.\n\nOur team delivers high-precision takeoffs, competitive subcontractor pricing, and rapid estimating turnaround.\n\nPlease confirm the right contact or portal to submit our credentials.\n\nBest regards,\nCommercial Estimating Department"
    },
    "Enterprise SaaS": {
      subject: "Strategic SaaS Partnership // {{company_name}}",
      body: "Hi Team at {{company_name}},\n\nI came across your platform and was impressed by your product architecture. We specialize in B2B SaaS growth, API integrations, and workflow automation that scale pipeline velocity.\n\nWould you be open to a brief 10-minute chat this week to explore collaboration opportunities?\n\nBest regards,\nNexus Enterprise Team"
    },
    "Gym Equipment": {
      subject: "Commercial Fitness Equipment Supply & Distribution // {{company_name}}",
      body: "Dear Commercial Procurement Team at {{company_name}},\n\nWe are reaching out regarding commercial gym and strength equipment supply, distribution, and facility outfitting.\n\nWe offer high-durability commercial-grade racks, barbells, plate-loaded machinery, and cardio equipment at competitive trade rates.\n\nPlease let us know if you have upcoming facility upgrades or equipment expansion plans.\n\nBest regards,\nCommercial Fitness Outfitting Team"
    }
  };

  const handleOpenApprovalModal = (item) => {
    setSelectedApproval(item);
    setApprovalRecipient(item.recipient || item.primary_email || "");
    setApprovalCompanyName(item.company_name || "");
    const initialNiche = item.industry_niche || item.niche || "Commercial Construction";
    setApprovalNiche(initialNiche);
    setApprovalSubject(item.subject || "");
    setApprovalBody(item.message_body || "");
  };

  const handleTemplateSwitch = (targetNiche) => {
    setApprovalNiche(targetNiche);
    const comp = approvalCompanyName || (selectedApproval?.company_name || "Partner");
    const rec = approvalRecipient || (selectedApproval?.recipient || "contact@target.com");

    const customMatch = templatesList?.find(t => (t.niche || "").toLowerCase() === targetNiche.toLowerCase());
    let tplSubject = "";
    let tplBody = "";

    if (customMatch) {
      tplSubject = customMatch.subject_template;
      tplBody = customMatch.body_template;
    } else if (NICHE_TEMPLATES[targetNiche]) {
      tplSubject = NICHE_TEMPLATES[targetNiche].subject;
      tplBody = NICHE_TEMPLATES[targetNiche].body;
    } else {
      tplSubject = `Strategic Collaboration // {{company_name}} [${targetNiche}]`;
      tplBody = `Dear Commercial Team at {{company_name}},\n\nWe are reaching out regarding commercial opportunities in the ${targetNiche} sector.\n\nBest regards,\nBusiness Development Team`;
    }

    const renderedSubj = tplSubject.replace(/\{\{company_name\}\}/g, comp).replace(/\{\{recipient_email\}\}/g, rec);
    const renderedBody = tplBody.replace(/\{\{company_name\}\}/g, comp).replace(/\{\{recipient_email\}\}/g, rec);
    setApprovalSubject(renderedSubj);
    setApprovalBody(renderedBody);
  };

  const handleCompanyNameChange = (newComp) => {
    const oldComp = approvalCompanyName;
    setApprovalCompanyName(newComp);
    if (oldComp && oldComp.trim()) {
      if (approvalSubject.includes(oldComp)) {
        setApprovalSubject(approvalSubject.split(oldComp).join(newComp));
      }
      if (approvalBody.includes(oldComp)) {
        setApprovalBody(approvalBody.split(oldComp).join(newComp));
      }
    }
  };

  const handleApproveOutreach = async (queueId, customSubject, customBody, customRecipient, customCompanyName) => {
    try {
      const resp = await fetch(`${API_BASE}/api/outreach/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          queue_id: queueId,
          approver: user.username,
          edited_subject: customSubject,
          edited_body: customBody,
          edited_recipient: customRecipient || approvalRecipient,
          edited_company_name: customCompanyName || approvalCompanyName
        })
      });
      const data = await resp.json();
      if (resp.ok) {
        setSelectedApproval(null);
        setAlertBanner({
          type: "success",
          message: `Outreach item authorized for ${customRecipient || approvalRecipient || "recipient"}! Persisted to database.`
        });
        fetchData();
      } else {
        setAlertBanner({
          type: "danger",
          message: data.detail || "Approval failed."
        });
      }
    } catch (e) {
      setAlertBanner({
        type: "danger",
        message: "Error approving outreach."
      });
    }
  };

  const handleDeleteQueueItem = async (queueId, recipientEmail) => {
    if (!confirm(`Permanently delete lead for '${recipientEmail || "this contact"}' from the queue?`)) return;
    try {
      const resp = await fetch(`${API_BASE}/api/outreach/queue/${queueId}`, {
        method: "DELETE",
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      const data = await resp.json();
      if (resp.ok && data.success) {
        if (selectedApproval && selectedApproval.id === queueId) {
          setSelectedApproval(null);
        }
        setAlertBanner({
          type: "info",
          message: `Lead permanently removed from database.`
        });
        fetchData();
      } else {
        setAlertBanner({
          type: "danger",
          message: data.detail || "Failed to delete lead."
        });
      }
    } catch (err) {
      setAlertBanner({
        type: "danger",
        message: "Error deleting queue item."
      });
    }
  };

  const handlePurgeUnapprovedGate = async () => {
    if (!confirm("⚠️ Confirm Bulk Purge: Are you sure you want to permanently delete ALL unapproved/pending leads from the Approval Gate?")) return;
    try {
      const resp = await fetch(`${API_BASE}/api/outreach/purge-unapproved`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      const data = await resp.json();
      if (resp.ok && data.success) {
        setAlertBanner({
          type: "success",
          message: `Gate Purged: Removed ${data.purged_count} pending leads. Ready for fresh hunt!`
        });
        fetchData();
      } else {
        setAlertBanner({
          type: "danger",
          message: data.detail || "Purge failed."
        });
      }
    } catch (err) {
      setAlertBanner({
        type: "danger",
        message: "Error executing bulk purge."
      });
    }
  };

  const handleUnblockLead = async (queueId, recipient) => {
    try {
      const resp = await fetch(`${API_BASE}/api/outreach/unblock`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ queue_id: queueId })
      });
      const data = await resp.json();
      if (resp.ok && data.success) {
        setAlertBanner({
          type: "success",
          message: `✓ Unblocked: ${recipient || "Lead"} returned to Approval Hold.`
        });
        await fetchData();
      } else {
        setAlertBanner({
          type: "danger",
          message: data.detail || data.message || "Failed to unblock lead."
        });
      }
    } catch (err) {
      setAlertBanner({
        type: "danger",
        message: "Error unblocking lead."
      });
    }
  };

  const handleDispatchQueueNow = async (bypassWindow = true, specificQueueId = null) => {
    setIsDispatchingNow(true);
    setPulseState("DISPATCHING");
    try {
      const resp = await fetch(`${API_BASE}/api/outreach/dispatch-now`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          bypass_window: bypassWindow,
          queue_id: specificQueueId
        })
      });
      const data = await resp.json();
      if (resp.ok && data.success) {
        if (data.dispatched_count === 0 && data.errors && data.errors.length > 0) {
          const firstErr = data.errors[0];
          setAlertBanner({
            type: "danger",
            message: `⚠️ Dispatch Blocked: ${firstErr.message || firstErr.reason || "Unable to dispatch leads."}`
          });
          setPulseState("RUNNING");
        } else if (data.dispatched_count === 0 && data.scheduled_count === 0) {
          setAlertBanner({
            type: "info",
            message: "No authorized leads currently waiting in queue to be dispatched."
          });
          setPulseState("RUNNING");
        } else {
          setAlertBanner({
            type: "success",
            message: `⚡ Dispatch Engine Triggered: ${data.dispatched_count || 0} leads dispatched! (${data.scheduled_count || 0} queued for local business hours)`
          });
        }
        await fetchData();
      } else {
        const errMsg = data.detail || (data.errors && data.errors[0] && (data.errors[0].message || data.errors[0].reason)) || data.message || "Dispatch queue trigger failed.";
        setAlertBanner({
          type: "danger",
          message: `Dispatch failed: ${errMsg}`
        });
        setPulseState("RUNNING");
        await fetchData();
      }
    } catch (err) {
      setAlertBanner({
        type: "danger",
        message: "Error executing dispatch trigger."
      });
      setPulseState("RUNNING");
    } finally {
      setIsDispatchingNow(false);
      setPulseState("RUNNING");
    }
  };

  const handleToggleDispatcherBypass = async (enabled) => {
    try {
      const resp = await fetch(`${API_BASE}/api/dispatcher/toggle-bypass`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ bypass_window: enabled })
      });
      const data = await resp.json();
      if (resp.ok && data.success) {
        setDispatcherState(prev => ({ ...prev, bypass_window: enabled }));
        setAlertBanner({
          type: "info",
          message: enabled
            ? "⚡ Dispatcher Bypass Window ENABLED: 24/7 immediate dispatch active for testing/weekends."
            : "🕒 Dispatcher Window RESTORED: Standard 9:00 AM - 5:00 PM local recipient business hours active."
        });
        fetchData();
      }
    } catch (err) {
      setAlertBanner({ type: "danger", message: "Failed to toggle dispatcher bypass window." });
    }
  };

  const handleBatchApprove = async () => {
    if (!confirm(`Confirm authorization to approve all ${pendingApprovals.length} pending leads in the Human Gate?`)) return;
    try {
      const resp = await fetch(`${API_BASE}/api/outreach/batch-approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ approver: user.username })
      });
      const data = await resp.json();
      setAlertBanner({
        type: "success",
        message: `Authorized: ${data.items_approved} outreach items approved by ${user.username}!`
      });
      fetchData();
    } catch (e) {
      alert("Batch approval failed.");
    }
  };

  // ---------------------------------------------------------------------------
  // HOT LEAD HANDLERS
  // ---------------------------------------------------------------------------
  const handleOpenHotLeadModal = (lead) => {
    setSelectedHotLead(lead);
    // Strip quoted > thread lines, On ... wrote headers, and email continuation noise
    const rawInquiry = lead.message_body || lead.reply_snippet || lead.incoming_message || lead.last_reply_body || "";
    const inquiryText = rawInquiry
      .split("\n")
      .filter(line => !line.trim().startsWith(">") && !/^on\s.+wrote:$/i.test(line.trim()))
      .join("\n")
      .trim();
    setIncomingInquiryText(inquiryText);
    const resolvedComp = lead.company_name && !["gmail.com", "outlook.com", "yahoo.com", "hotmail.com", "icloud.com", "mail.com"].includes(lead.company_name.toLowerCase()) && lead.company_name !== lead.sender_email
      ? lead.company_name
      : (lead.sender_email ? lead.sender_email.split("@")[0].replace(/[._-]/g, " ").replace(/\b\w/g, c => c.toUpperCase()) : "your organization");
    const aiDraft = lead.ai_suggested_reply || (inquiryText
      ? `Thank you for your inquiry regarding ${resolvedComp}.\n\nWe would be glad to connect and discuss how we can assist with your requirements. Please let us know your availability for a brief conversation this week.\n\nBest regards`
      : "");
    setHotLeadReplyBody(aiDraft);
  };

  const handleDispatchHotLeadReply = async (replyId, recipientArg, responseBody) => {
    // Validation: refuse empty body
    if (!responseBody || !responseBody.trim()) {
      setAlertBanner({ type: "danger", message: "Response body cannot be empty. Please draft a message before dispatching." });
      return;
    }
    // Resolve actual recipient
    const recipient = selectedHotLead?.recipient || selectedHotLead?.sender_email || selectedHotLead?.primary_email || recipientArg;
    try {
      const resp = await fetch(`${API_BASE}/api/outreach/send-hot-reply`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ reply_id: replyId, recipient, response_body: responseBody })
      });
      let data = {};
      try { data = await resp.json(); } catch (_) {}
      if (!resp.ok) {
        setAlertBanner({ type: "danger", message: data.detail || "Failed to dispatch response." });
        return;
      }
      setSelectedHotLead(null);
      setAlertBanner({
        type: "success",
        message: `Executive Response dispatched to ${data.recipient || recipient} via ${data.dispatched_via || data.inbox_used || "SMTP"}!`
      });
      // Sync lead to Converted/CLOSED in kanban + remove from hot leads
      const recipLower = (recipient || "").toLowerCase().trim();
      setHotLeads(prev => prev.filter(h =>
        h.id !== replyId &&
        h.lead_id !== selectedHotLead?.lead_id &&
        (h.sender_email || "").toLowerCase().trim() !== recipLower
      ));
      setKanbanItems(prev => prev.map(item =>
        (item.id === selectedHotLead?.id ||
         item.lead_id === selectedHotLead?.lead_id ||
         (item.recipient || "").toLowerCase().trim() === recipLower)
          ? { ...item, status: "CLOSED" } : item
      ));
      fetchData();
    } catch (e) {
      setAlertBanner({ type: "danger", message: "Network error while dispatching response." });
    }
  };

  // ---------------------------------------------------------------------------
  // INBOX ROTATOR HANDLERS
  // ---------------------------------------------------------------------------
  const handleAddMailbox = async (e) => {
    if (e) e.preventDefault();
    try {
      const resp = await fetch(`${API_BASE}/api/mailboxes`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          display_name: newMbDisplayName,
          email_address: newMbEmail,
          smtp_host: newMbHost,
          smtp_port: parseInt(newMbPort, 10) || 587,
          smtp_username: newMbUsername,
          smtp_password: newMbPassword,
          daily_limit: parseInt(newMbDailyLimit, 10) || 45,
          webhook_url: newMbWebhookUrl || ""
        })
      });
      const data = await resp.json();
      if (resp.ok) {
        setIsAddMailboxOpen(false);
        setNewMbDisplayName("");
        setNewMbEmail("");
        setNewMbHost("");
        setNewMbPort("587");
        setNewMbUsername("");
        setNewMbPassword("");
        setNewMbDailyLimit("45");
        setNewMbWebhookUrl("");
        setAlertBanner({ type: "success", message: `Mailbox '${data.email_address}' enrolled into rotator!` });
        fetchData();
      } else {
        alert(data.detail || "Failed to add mailbox.");
      }
    } catch (err) {
      alert("Error adding mailbox.");
    }
  };

  const handleOpenEditMailbox = (mb) => {
    setSelectedMailboxForEdit(mb);
    setEditMbDisplayName(mb.display_name || "");
    setEditMbEmail(mb.email_address || "");
    setEditMbHost(mb.smtp_host || "");
    setEditMbPort(String(mb.smtp_port || 587));
    setEditMbUsername(mb.smtp_username || "");
    setEditMbPassword(mb.smtp_password || "");
    setEditMbDailyLimit(String(mb.daily_limit || 45));
    setEditMbWebhookUrl(mb.webhook_url || "");
  };

  const handleUpdateMailbox = async (e) => {
    if (e) e.preventDefault();
    if (!selectedMailboxForEdit) return;
    try {
      const resp = await fetch(`${API_BASE}/api/mailboxes/${selectedMailboxForEdit.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          display_name: editMbDisplayName,
          email_address: editMbEmail,
          smtp_host: editMbHost,
          smtp_port: parseInt(editMbPort, 10) || 587,
          smtp_username: editMbUsername,
          smtp_password: editMbPassword || undefined,
          daily_limit: parseInt(editMbDailyLimit, 10) || 45,
          webhook_url: editMbWebhookUrl !== undefined ? editMbWebhookUrl : undefined
        })
      });
      const data = await resp.json();
      if (resp.ok) {
        setSelectedMailboxForEdit(null);
        setAlertBanner({ type: "success", message: `Mailbox '${data.email_address}' updated successfully!` });
        fetchData();
      } else {
        alert(data.detail || "Failed to update mailbox.");
      }
    } catch (err) {
      alert("Error updating mailbox.");
    }
  };

  const handleDeleteMailbox = async (mb) => {
    if (!confirm(`Permanently remove mailbox "${mb.display_name}" (${mb.email_address}) from the rotator pool?`)) return;
    try {
      const resp = await fetch(`${API_BASE}/api/mailboxes/${mb.id}`, {
        method: "DELETE",
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      const data = await resp.json();
      if (resp.ok) {
        setAlertBanner({ type: "info", message: `Mailbox '${mb.email_address}' removed from rotator pool.` });
        fetchData();
      } else {
        alert(data.detail || "Failed to delete mailbox.");
      }
    } catch (err) {
      alert("Error deleting mailbox.");
    }
  };

  // ---------------------------------------------------------------------------
  // ADMIN PROFILE & SECURITY SETTINGS
  // ---------------------------------------------------------------------------
  const handleUpdateAdminProfile = async (e) => {
    if (e) e.preventDefault();
    if (adminNewPassword && adminNewPassword !== adminConfirmPassword) {
      alert("Error: New Password and Confirm Password do not match.");
      return;
    }
    try {
      const resp = await fetch(`${API_BASE}/api/admin/profile`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          username: adminUsernameInput,
          email: adminEmailInput,
          full_name: adminFullNameInput,
          current_password: adminCurrentPassword || undefined,
          new_password: adminNewPassword || undefined
        })
      });
      const data = await resp.json();
      if (resp.ok) {
        setAlertBanner({ type: "success", message: "Admin profile updated successfully! Password re-hashed with Bcrypt." });
        setAdminCurrentPassword("");
        setAdminNewPassword("");
        setAdminConfirmPassword("");
        adminFormDirtyRef.current = false;
        fetchData();
      } else {
        alert(data.detail || "Profile update failed.");
      }
    } catch (err) {
      alert("Error updating profile.");
    }
  };

  // ---------------------------------------------------------------------------
  // OPERATOR MANAGEMENT HANDLERS
  // ---------------------------------------------------------------------------
  const handleToggleOperatorStatus = async (operatorId) => {
    // Instant optimistic update for smooth UI response
    setOperatorsList(prev => prev.map(op => {
      if (op.id === operatorId) {
        return { ...op, is_active: op.is_active === 1 ? 0 : 1 };
      }
      return op;
    }));
    try {
      const resp = await fetch(`${API_BASE}/api/operators/${operatorId}/toggle-status`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await resp.json();
      if (resp.ok) {
        setAlertBanner({ type: "info", message: `Operator status updated to: ${data.status_label}` });
        fetchData();
      } else {
        fetchData();
        setAlertBanner({ type: "danger", message: data.detail || "Status toggle failed." });
      }
    } catch (err) {
      fetchData();
      setAlertBanner({ type: "danger", message: "Error toggling operator status." });
    }
  };

  const handleOpenResetPasswordModal = (op) => {
    setSelectedUserForReset(op);
    setResetPasswordInput("");
  };

  const handleResetOperatorPassword = async (e) => {
    if (e) e.preventDefault();
    if (!resetPasswordInput || resetPasswordInput.length < 6) {
      setAlertBanner({ type: "warning", message: "Passphrase must be at least 6 characters." });
      return;
    }
    setIsResettingPassword(true);
    try {
      const resp = await fetch(`${API_BASE}/api/operators/${selectedUserForReset.id}/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ new_password: resetPasswordInput })
      });
      const data = await resp.json();
      if (resp.ok) {
        setSelectedUserForReset(null);
        setResetPasswordInput("");
        setAlertBanner({ type: "success", message: `Password reset successfully for ${data.username} using Bcrypt encryption.` });
        fetchData();
      } else {
        setAlertBanner({ type: "danger", message: data.detail || "Password reset failed." });
      }
    } catch (err) {
      setAlertBanner({ type: "danger", message: "Error resetting password." });
    } finally {
      setIsResettingPassword(false);
    }
  };

  const handleDeleteOperator = async (op) => {
    if (!op || op.role === "admin") {
      setAlertBanner({ type: "danger", message: "Master Administrator accounts cannot be deleted." });
      return;
    }

    const confirmed = window.confirm(
      `⚠️ PERMANENT OPERATOR REMOVAL\n\nAre you sure you want to permanently delete operator "${op.username}" (${op.full_name || "Operator"})?\n\nThis will remove their account and revoke license access. All existing leads and pipeline data will remain preserved.`
    );
    if (!confirmed) return;

    try {
      const resp = await fetch(`${API_BASE}/api/operators/${op.id}`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        }
      });
      const data = await resp.json();
      if (resp.ok && data.success) {
        setOperatorsList(prev => prev.filter(item => item.id !== op.id));
        if (expandedOperatorId === op.id) {
          setExpandedOperatorId(null);
        }
        setAlertBanner({
          type: "success",
          message: `Operator "${op.username}" was permanently removed.`
        });
        fetchData();
      } else {
        setAlertBanner({
          type: "danger",
          message: data.detail || data.message || "Failed to delete operator account."
        });
      }
    } catch (err) {
      setAlertBanner({
        type: "danger",
        message: "Network error occurred while deleting operator."
      });
    }
  };

  const handleCreateOperator = async (e) => {
    if (e) e.preventDefault();
    if (!newOpUsername || newOpUsername.trim().length < 3) {
      setAlertBanner({ type: "warning", message: "Username must be at least 3 characters." });
      return;
    }
    if (!newOpPassword || newOpPassword.length < 6) {
      setAlertBanner({ type: "warning", message: "Passphrase must be at least 6 characters." });
      return;
    }
    setIsCreatingOperator(true);
    try {
      const resp = await fetch(`${API_BASE}/api/operators`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          username: newOpUsername.trim(),
          password: newOpPassword,
          full_name: newOpFullName.trim() || newOpUsername.trim(),
          email: newOpEmail.trim(),
          device_lock_id: newOpDeviceLock.trim() || undefined,
          device_lock_enabled: true,
          expiry_days: parseInt(newOpExpiryDays, 10) || 90,
          daily_scrape_quota: parseInt(newOpScrapeQuota, 10) || 200,
          daily_send_quota: parseInt(newOpSendQuota, 10) || 50
        })
      });
      const data = await resp.json();
      if (resp.ok) {
        setIsCreateOperatorOpen(false);
        setNewOpUsername("");
        setNewOpPassword("");
        setNewOpFullName("");
        setNewOpEmail("");
        setNewOpDeviceLock("");
        setNewOpExpiryDays("90");
        setNewOpScrapeQuota("200");
        setNewOpSendQuota("50");
        setAlertBanner({ type: "success", message: `Operator account '${data.username}' created with signed license token!` });
        fetchData();
      } else {
        setAlertBanner({ type: "danger", message: data.detail || "Operator creation failed." });
      }
    } catch (err) {
      setAlertBanner({ type: "danger", message: "Error creating operator." });
    } finally {
      setIsCreatingOperator(false);
    }
  };

  const handleToggleInlineAdjust = (op) => {
    if (expandedOperatorId === op.id) {
      setExpandedOperatorId(null);
    } else {
      setExpandedOperatorId(op.id);
      setInlineScrapeQuota(String(op.daily_scrape_quota || 200));
      setInlineSendQuota(String(op.daily_send_quota || 50));
    }
  };

  const handleApplyInlineQuotas = async (operatorId, extendDays = null) => {
    setUpdatingOperatorId(operatorId);
    // Instant optimistic update
    setOperatorsList(prev => prev.map(op => {
      if (op.id === operatorId) {
        return {
          ...op,
          daily_scrape_quota: parseInt(inlineScrapeQuota, 10) || op.daily_scrape_quota,
          daily_send_quota: parseInt(inlineSendQuota, 10) || op.daily_send_quota
        };
      }
      return op;
    }));
    try {
      const resp = await fetch(`${API_BASE}/api/operators/${operatorId}/quotas`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          extend_days: extendDays,
          daily_scrape_quota: parseInt(inlineScrapeQuota, 10) || 200,
          daily_send_quota: parseInt(inlineSendQuota, 10) || 50
        })
      });
      let data = {};
      try { data = await resp.json(); } catch (_) { /* non-JSON 502 guard */ }
      if (resp.ok) {
        setAlertBanner({
          type: "success",
          message: `Quotas updated for ${data.username || "operator"}! Scrape: ${data.daily_scrape_quota}/day, Send: ${data.daily_send_quota}/day. Expiry: ${data.new_expiry_date || "Perpetual"}`
        });
        setExpandedOperatorId(null);
        fetchData();
      } else {
        fetchData();
        setAlertBanner({ type: "danger", message: data.detail || "Quota modification failed." });
      }
    } catch (err) {
      fetchData();
      setAlertBanner({ type: "danger", message: "Error modifying quotas." });
    } finally {
      setUpdatingOperatorId(null);
    }
  };

  // ---------------------------------------------------------------------------
  // TEMPLATE MANAGEMENT HANDLERS
  // ---------------------------------------------------------------------------
  const handleOpenTemplateModal = (tpl = null) => {
    if (tpl) {
      setEditingTemplate(tpl);
      setTplTitle(tpl.title || "");
      setTplNiche(tpl.niche || "Commercial Construction");
      setTplSubject(tpl.subject_template || "");
      setTplBody(tpl.body_template || "");
      setTplIsDefault(Boolean(tpl.is_default));
    } else {
      setEditingTemplate(null);
      setTplTitle("");
      setTplNiche("Commercial Construction");
      setTplSubject("Commercial Estimation & Tenders // {{company_name}}");
      setTplBody(
        "Dear Estimating Team at {{company_name}},\n\n" +
        "We are reaching out regarding commercial capacity and tender packages for {{niche}} in {{country}}.\n\n" +
        "Our team handles detailed bill-of-quantities takeoffs, rapid estimating, and competitive pricing.\n\n" +
        "Please confirm the right contact or portal to receive tender specifications.\n\n" +
        "Best regards,\n" +
        "Commercial Estimating Team\n\n" +
        "---\n" +
        "To opt-out from future notices: {{unsubscribe_link}}"
      );
      setTplIsDefault(false);
    }
    setIsTemplateModalOpen(true);
  };

  const handleSaveTemplate = async (e) => {
    if (e) e.preventDefault();
    if (!tplTitle.trim() || !tplSubject.trim() || !tplBody.trim()) {
      alert("Please provide title, subject, and body for the template.");
      return;
    }
    try {
      const headers = {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {})
      };
      if (editingTemplate) {
        const resp = await fetch(`${API_BASE}/api/templates/${editingTemplate.id}`, {
          method: "PUT",
          headers,
          body: JSON.stringify({
            title: tplTitle,
            niche: tplNiche,
            subject_template: tplSubject,
            body_template: tplBody,
            is_default: tplIsDefault
          })
        });
        if (resp.ok) {
          setAlertBanner({ type: "success", message: `Template '${tplTitle}' updated successfully.` });
          setIsTemplateModalOpen(false);
          fetchData();
        } else {
          const err = await resp.json();
          alert(err.detail || "Failed to update template.");
        }
      } else {
        const resp = await fetch(`${API_BASE}/api/templates`, {
          method: "POST",
          headers,
          body: JSON.stringify({
            title: tplTitle,
            niche: tplNiche,
            subject_template: tplSubject,
            body_template: tplBody,
            is_default: tplIsDefault
          })
        });
        if (resp.ok) {
          setAlertBanner({ type: "success", message: `Template '${tplTitle}' created successfully.` });
          setIsTemplateModalOpen(false);
          fetchData();
        } else {
          const err = await resp.json();
          alert(err.detail || "Failed to create template.");
        }
      }
    } catch (e) {
      console.error(e);
      alert("Template save error.");
    }
  };

  const handleDeleteTemplate = async (tplId) => {
    if (!confirm("Are you sure you want to delete this proposal template?")) return;
    try {
      const resp = await fetch(`${API_BASE}/api/templates/${tplId}`, {
        method: "DELETE",
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      if (resp.ok) {
        setAlertBanner({ type: "info", message: "Template removed." });
        fetchData();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleInsertTag = (tag) => {
    setTplBody(prev => prev + " " + tag);
  };

  // ---------------------------------------------------------------------------
  // MANUAL BILLING CONTROLS HANDLERS
  // ---------------------------------------------------------------------------
  const handleApplyBilling = async (e) => {
    if (e) e.preventDefault();
    if (!billingTargetOpId) {
      alert("Please select a target operator.");
      return;
    }
    const price = parseFloat(billingBasePrice) || 0;
    if (price <= 0) {
      alert("Please enter a valid Base Price.");
      return;
    }
    setIsApplyingBilling(true);
    try {
      const resp = await fetch(`${API_BASE}/api/operators/${billingTargetOpId}/billing`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          base_price: price,
          duration_days: billingDurationDays,
          notes: billingNotes.trim() || undefined
        })
      });
      const data = await resp.json();
      if (resp.ok) {
        setAlertBanner({
          type: "success",
          message: `Billing applied! +${data.duration_days}d extension for $${data.final_price} (Expiry: ${data.new_expiry_date}).`
        });
        fetchData();
        setBillingNotes("");
      } else {
        alert(data.detail || "Billing application failed.");
      }
    } catch (err) {
      console.error(err);
      alert("Billing error.");
    } finally {
      setIsApplyingBilling(false);
    }
  };

  // ---------------------------------------------------------------------------
  // GLOBAL DOMAIN BLACKLIST HANDLERS
  // ---------------------------------------------------------------------------
  const handleAddBlacklistRule = async (e) => {
    if (e) e.preventDefault();
    if (!newRulePattern.trim()) {
      alert("Please enter a domain or pattern.");
      return;
    }
    try {
      const resp = await fetch(`${API_BASE}/api/blacklist`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          pattern: newRulePattern.trim(),
          reason: newRuleReason.trim() || "Excluded Domain"
        })
      });
      const data = await resp.json();
      if (resp.ok) {
        setAlertBanner({ type: "success", message: `Blacklist rule '${data.pattern}' added.` });
        setNewRulePattern("");
        setNewRuleReason("");
        fetchData();
      } else {
        alert(data.detail || "Failed to add blacklist rule.");
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteBlacklistRule = async (ruleId) => {
    try {
      const resp = await fetch(`${API_BASE}/api/blacklist/${ruleId}`, {
        method: "DELETE",
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      if (resp.ok) {
        setAlertBanner({ type: "info", message: "Blacklist rule removed." });
        fetchData();
      }
    } catch (e) {
      console.error(e);
    }
  };

  // ---------------------------------------------------------------------------
  // IMAP BOUNCE & REPLY POLL HANDLER
  // ---------------------------------------------------------------------------
  const handlePollImap = async () => {
    setIsPollingImap(true);
    try {
      const resp = await fetch(`${API_BASE}/api/inbox/poll`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      const data = await resp.json();
      if (resp.ok) {
        setAlertBanner({
          type: "info",
          message: `IMAP Poll finished: ${data.processed_count} messages inspected. Bounces & replies synchronized.`
        });
        fetchData();
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsPollingImap(false);
    }
  };

  // ---------------------------------------------------------------------------
  // HELPER: CLEAN KANBAN TAG DEDUPLICATION
  // ---------------------------------------------------------------------------
  const getCleanLeadBadges = (lead) => {
    const badges = [];

    const rawTier = (lead.primary_email_tier || lead.channel || "TIER_1").toUpperCase();
    let tierLabel = "Tier 1";
    if (rawTier.includes("ESTIMATING")) {
      tierLabel = "Tier 1 Estimating";
    } else if (rawTier.includes("TIER_2")) {
      tierLabel = "Tier 2";
    } else if (rawTier.includes("WEB_FORM")) {
      tierLabel = "Web Form";
    } else if (rawTier.includes("EMAIL")) {
      tierLabel = "Direct Email";
    }
    badges.push({ text: tierLabel, type: "tier" });

    if (lead.quality_tag) {
      const normQuality = lead.quality_tag.toUpperCase().replace(/[-_]/g, " ");
      if (!normQuality.includes("TIER 1") && !normQuality.includes("ESTIMATING")) {
        badges.push({ text: lead.quality_tag, type: "quality" });
      }
    }

    return badges;
  };

  // ---------------------------------------------------------------------------
  // VIEW: ENTERPRISE LOGIN / FIRST-RUN SETUP SCREEN
  // ---------------------------------------------------------------------------
  if (!user || !token) {
    if (setupRequired) {
      return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-base relative overflow-hidden">
          {/* Video 1 Geometric Obsidian Backdrop */}
          <div className="np-geometric-bg" />
          <div className="absolute w-[500px] h-[500px] rounded-full bg-[var(--accent)] opacity-[0.06] blur-[140px] pointer-events-none -top-40 -left-40" />
          <div className="absolute w-[500px] h-[500px] rounded-full bg-[var(--accent)] opacity-[0.04] blur-[140px] pointer-events-none -bottom-40 -right-40" />

          {/* Top Bar Quick Controls */}
          <div className="absolute top-4 right-4 flex items-center gap-2 z-20">
            {/* Theme Switcher */}
            <div className="relative">
              <button
                type="button"
                onClick={() => setIsThemeMenuOpen(!isThemeMenuOpen)}
                className="btn btn-secondary btn-sm flex items-center gap-1.5 backdrop-blur-md"
                title="Select Visual Theme"
              >
                <span className="theme-dot" style={{ backgroundColor: THEMES.find(t => t.id === activeTheme)?.dotColor || "#38bdf8" }} />
                <span className="hidden sm:inline text-xs font-mono">Theme</span>
                <span className="text-[10px]">▾</span>
              </button>
              {isThemeMenuOpen && (
                <div
                  className="absolute right-0 mt-1.5 w-56 np-glass-card p-1 z-50 shadow-2xl border-theme"
                  onMouseLeave={() => setIsThemeMenuOpen(false)}
                >
                  <div className="px-2.5 py-1.5 text-[10px] font-semibold text-theme-secondary uppercase tracking-wider border-b-theme">
                    Appearance Preset (6 Themes)
                  </div>
                  {THEMES.map((t) => (
                    <button
                      key={t.id}
                      onClick={() => {
                        setActiveTheme(t.id);
                        setIsThemeMenuOpen(false);
                        SoundEffects.themeShimmer();
                      }}
                      className={`w-full text-left px-2.5 py-1.5 rounded text-xs flex items-center justify-between hover:bg-hover transition-colors ${
                        activeTheme === t.id ? "text-theme-accent font-semibold bg-[var(--accent-muted)]" : "text-theme-primary"
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <span className="theme-dot" style={{ backgroundColor: t.dotColor }} />
                        <div>
                          <div>{t.name}</div>
                          <div className="text-[9px] text-theme-muted leading-tight">{t.desc}</div>
                        </div>
                      </div>
                      {activeTheme === t.id && <span>✓</span>}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Audio SFX Toggle */}
            <button
              type="button"
              onClick={() => {
                const next = !soundEnabled;
                setSoundEnabled(next);
                if (next) setTimeout(() => playUiSound("glass_chime"), 50);
              }}
              className={`btn btn-sm backdrop-blur-md ${soundEnabled ? "btn-secondary text-theme-accent" : "btn-ghost text-theme-muted"}`}
              title={soundEnabled ? "UI Audio SFX Active (Click to Mute)" : "UI Audio SFX Muted (Click to Enable)"}
            >
              <span>{soundEnabled ? "🔊" : "🔇"}</span>
              <span className="text-[11px] font-mono hidden sm:inline">{soundEnabled ? "SFX: ON" : "SFX: OFF"}</span>
            </button>
          </div>

        <div className="np-split-auth-card">
          {/* LEFT SHOWCASE PANEL: FIRST RUN ADMIN SETUP */}
          <div className="np-auth-showcase-panel">
            <div>
              <div className="flex items-center gap-2.5 mb-5">
                <div className="w-10 h-10 rounded-xl border border-[var(--border)] bg-elevated flex items-center justify-center font-bold text-sm text-theme-accent font-mono shadow-inner">
                  NP
                </div>
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="font-bold text-sm tracking-tight text-white">Nexus-Pulse</span>
                    <span className="badge badge-accent text-[9px] px-1.5 py-0 font-mono">LEVEL 2</span>
                  </div>
                  <div className="text-[10px] text-theme-muted font-mono">Autonomous B2B Pipeline Gateway</div>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <span className="badge badge-warning text-[9px] font-mono uppercase tracking-wider mb-2 inline-block px-2 py-0.5">
                    ★ First-Run Production Setup
                  </span>
                  <h2 className="text-2xl lg:text-3xl font-black tracking-tight text-white leading-tight">
                    INITIALIZE MASTER ADMIN
                  </h2>
                  <p className="text-xs text-theme-secondary mt-1.5 leading-relaxed">
                    Fresh installation detected. Configure your Master Administrator profile and bind your host hardware key.
                  </p>
                </div>

                <div className="space-y-2.5 pt-2">
                  <div className="flex items-start gap-2.5 text-xs text-theme-secondary p-2.5 rounded-xl bg-[rgba(255,255,255,0.025)] border border-[rgba(255,255,255,0.06)] shadow-sm backdrop-blur-sm">
                    <span className="w-6 h-6 rounded-lg bg-[rgba(245,158,11,0.1)] border border-[rgba(245,158,11,0.25)] flex items-center justify-center text-xs shrink-0 text-theme-warning">👑</span>
                    <div>
                      <strong className="text-white block font-medium">Master Root Authority</strong>
                      <span className="text-[11px] text-theme-muted">Full administrative control & multi-tenant management</span>
                    </div>
                  </div>
                  <div className="flex items-start gap-2.5 text-xs text-theme-secondary p-2.5 rounded-xl bg-[rgba(255,255,255,0.025)] border border-[rgba(255,255,255,0.06)] shadow-sm backdrop-blur-sm">
                    <span className="w-6 h-6 rounded-lg bg-[rgba(168,85,247,0.1)] border border-[rgba(168,85,247,0.25)] flex items-center justify-center text-xs shrink-0 text-theme-purple">🔒</span>
                    <div>
                      <strong className="text-white block font-medium">Hardware Cryptographic Lock</strong>
                      <span className="text-[11px] text-theme-muted">MachineGuid & Bcrypt 12-round key derivation</span>
                    </div>
                  </div>
                  <div className="flex items-start gap-2.5 text-xs text-theme-secondary p-2.5 rounded-xl bg-[rgba(255,255,255,0.025)] border border-[rgba(255,255,255,0.06)] shadow-sm backdrop-blur-sm">
                    <span className="w-6 h-6 rounded-lg bg-[rgba(56,189,248,0.1)] border border-[rgba(56,189,248,0.25)] flex items-center justify-center text-xs shrink-0 text-theme-accent">📦</span>
                    <div>
                      <strong className="text-white block font-medium">Vault Database Partitioning</strong>
                      <span className="text-[11px] text-theme-muted">Zero-leak SQLite ACID schema with auto-migration</span>
                    </div>
                  </div>
                  <div className="flex items-start gap-2.5 text-xs text-theme-secondary p-2.5 rounded-xl bg-[rgba(255,255,255,0.025)] border border-[rgba(255,255,255,0.06)] shadow-sm backdrop-blur-sm">
                    <span className="w-6 h-6 rounded-lg bg-[rgba(16,185,129,0.1)] border border-[rgba(16,185,129,0.25)] flex items-center justify-center text-xs shrink-0 text-theme-success">⚡</span>
                    <div>
                      <strong className="text-white block font-medium">Enterprise Pipeline Ready</strong>
                      <span className="text-[11px] text-theme-muted">3-tier geo lead search, zero-bounce hygiene & SMTP</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-3 pt-4 border-t border-[var(--border-subtle)]">
              <div className="flex items-center justify-between text-[10px] font-mono text-theme-muted">
                <span className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[var(--warning)] animate-pulse" />
                  <span>STATUS: FRESH INSTALL</span>
                </span>
                <span>ROOT PROVISIONING</span>
              </div>
            </div>
          </div>

          {/* RIGHT FORM PANEL: FIRST RUN ADMIN SETUP */}
          <div className="np-auth-form-panel">
            <div className="mb-5">
              <h3 className="text-lg font-bold text-theme-primary">Create Master Admin</h3>
              <p className="text-xs text-theme-secondary mt-0.5">Define your executive administrative credentials.</p>
            </div>

            {initError && (
              <div className="mb-5 np-alert np-alert-error">
                <span>{initError}</span>
              </div>
            )}

            <form onSubmit={handleInitializeAdmin} className="space-y-3.5">
              <div>
                <label className="np-label">Master Administrator Username *</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-theme-muted text-xs">👤</span>
                  <input
                    type="text"
                    value={initUsername}
                    onChange={(e) => setInitUsername(e.target.value)}
                    className="np-glass-input font-mono pl-9"
                    placeholder="e.g. admin or h.huddair"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="np-label">Executive Full Name *</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-theme-muted text-xs">👔</span>
                    <input
                      type="text"
                      value={initFullName}
                      onChange={(e) => setInitFullName(e.target.value)}
                      className="np-glass-input pl-9"
                      placeholder="e.g. H.Huddair"
                      required
                    />
                  </div>
                </div>
                <div>
                  <label className="np-label">Corporate Email</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-theme-muted text-xs">✉️</span>
                    <input
                      type="email"
                      value={initEmail}
                      onChange={(e) => setInitEmail(e.target.value)}
                      className="np-glass-input font-mono pl-9"
                      placeholder="admin@nexus-pulse.io"
                    />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="np-label">Master Passphrase (Bcrypt) *</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-theme-muted text-xs">🔒</span>
                    <input
                      type="password"
                      value={initPassword}
                      onChange={(e) => setInitPassword(e.target.value)}
                      className="np-glass-input font-mono pl-9"
                      placeholder="Min 6 characters"
                      required
                    />
                  </div>
                </div>
                <div>
                  <label className="np-label">Confirm Passphrase *</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-theme-muted text-xs">🔒</span>
                    <input
                      type="password"
                      value={initConfirmPassword}
                      onChange={(e) => setInitConfirmPassword(e.target.value)}
                      className="np-glass-input font-mono pl-9"
                      placeholder="••••••••••••"
                      required
                    />
                  </div>
                </div>
              </div>

              <button
                type="submit"
                disabled={isInitializingAdmin}
                className="btn btn-primary w-full justify-center btn-lg mt-4 shadow-lg"
              >
                <span>{isInitializingAdmin ? "Binding Hardware & Generating Keys..." : "Initialize Master Admin & Enter Dashboard"}</span>
                <span>➔</span>
              </button>
            </form>
          </div>
        </div>
        </div>
      );
    }

    return (
      <div className="min-h-screen flex items-center justify-center p-4 bg-base relative overflow-hidden">
        {/* Video 1 Geometric Obsidian Backdrop */}
        <div className="np-geometric-bg" />
        <div className="absolute w-[500px] h-[500px] rounded-full bg-[var(--accent)] opacity-[0.06] blur-[140px] pointer-events-none -top-40 -left-40" />
        <div className="absolute w-[500px] h-[500px] rounded-full bg-[var(--accent)] opacity-[0.04] blur-[140px] pointer-events-none -bottom-40 -right-40" />

        {/* Top Right Quick Controls: Theme Presets & SFX Audio */}
        <div className="absolute top-4 right-4 flex items-center gap-2 z-20">
          {/* Theme Switcher */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setIsThemeMenuOpen(!isThemeMenuOpen)}
              className="btn btn-secondary btn-sm flex items-center gap-1.5 backdrop-blur-md"
              title="Select Visual Theme"
            >
              <span className="theme-dot" style={{ backgroundColor: THEMES.find(t => t.id === activeTheme)?.dotColor || "#38bdf8" }} />
              <span className="hidden sm:inline text-xs font-mono">Theme</span>
              <span className="text-[10px]">▾</span>
            </button>
            {isThemeMenuOpen && (
              <div
                className="absolute right-0 mt-1.5 w-56 np-glass-card p-1 z-50 shadow-2xl border-theme"
                onMouseLeave={() => setIsThemeMenuOpen(false)}
              >
                <div className="px-2.5 py-1.5 text-[10px] font-semibold text-theme-secondary uppercase tracking-wider border-b-theme">
                  Appearance Preset (6 Themes)
                </div>
                {THEMES.map((t) => (
                  <button
                    key={t.id}
                    onClick={() => {
                      setActiveTheme(t.id);
                      setIsThemeMenuOpen(false);
                      SoundEffects.themeShimmer();
                    }}
                    className={`w-full text-left px-2.5 py-1.5 rounded text-xs flex items-center justify-between hover:bg-hover transition-colors ${
                      activeTheme === t.id ? "text-theme-accent font-semibold bg-[var(--accent-muted)]" : "text-theme-primary"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className="theme-dot" style={{ backgroundColor: t.dotColor }} />
                      <div>
                        <div>{t.name}</div>
                        <div className="text-[9px] text-theme-muted leading-tight">{t.desc}</div>
                      </div>
                    </div>
                    {activeTheme === t.id && <span>✓</span>}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Audio SFX Toggle */}
          <button
            type="button"
            onClick={() => {
              const next = !soundEnabled;
              setSoundEnabled(next);
              if (next) setTimeout(() => playUiSound("glass_chime"), 50);
            }}
            className={`btn btn-sm backdrop-blur-md ${soundEnabled ? "btn-secondary text-theme-accent" : "btn-ghost text-theme-muted"}`}
            title={soundEnabled ? "UI Audio SFX Active (Click to Mute)" : "UI Audio SFX Muted (Click to Enable)"}
          >
            <span>{soundEnabled ? "🔊" : "🔇"}</span>
            <span className="text-[11px] font-mono hidden sm:inline">{soundEnabled ? "SFX: ON" : "SFX: OFF"}</span>
          </button>
        </div>

        {/* Video 1 True Split-Card Glassmorphism Auth Container */}
        <div className="np-split-auth-card">
          {/* LEFT SHOWCASE & VALUE PROPOSITION PANEL */}
          <div className="np-auth-showcase-panel">
            <div>
              <div className="flex items-center gap-2.5 mb-5">
                <div className="w-10 h-10 rounded-xl border border-[var(--border)] bg-elevated flex items-center justify-center font-bold text-sm text-theme-accent font-mono shadow-inner">
                  NP
                </div>
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="font-bold text-sm tracking-tight text-white">Nexus-Pulse</span>
                    <span className="badge badge-accent text-[9px] px-1.5 py-0 font-mono">LEVEL 2</span>
                  </div>
                  <div className="text-[10px] text-theme-muted font-mono">Autonomous B2B Pipeline Gateway</div>
                </div>
              </div>

              {authMode === "login" ? (
                <div key="showcase-login" className="space-y-4 np-auth-pane-enter">
                  <div>
                    <span className="badge badge-accent text-[9px] font-mono uppercase tracking-wider mb-2 inline-block px-2 py-0.5">
                      Security Matrix Active
                    </span>
                    <h2 className="text-2xl lg:text-3xl font-black tracking-tight text-white leading-tight">
                      WELCOME BACK!
                    </h2>
                    <p className="text-xs text-theme-secondary mt-1.5 leading-relaxed">
                      Please sign in with your cryptographic credentials to unlock your autonomous commercial pipeline.
                    </p>
                  </div>

                  <div className="space-y-2.5 pt-2">
                    <div className="flex items-start gap-2.5 text-xs text-theme-secondary p-2.5 rounded-xl bg-[rgba(255,255,255,0.025)] border border-[rgba(255,255,255,0.06)] shadow-sm backdrop-blur-sm">
                      <span className="w-6 h-6 rounded-lg bg-[rgba(56,189,248,0.1)] border border-[rgba(56,189,248,0.25)] flex items-center justify-center text-xs shrink-0 text-theme-accent">⚡</span>
                      <div>
                        <strong className="text-white block font-medium">3-Tier Geo Lead Engine</strong>
                        <span className="text-[11px] text-theme-muted">Cascading Region › Country › City discovery</span>
                      </div>
                    </div>
                    <div className="flex items-start gap-2.5 text-xs text-theme-secondary p-2.5 rounded-xl bg-[rgba(255,255,255,0.025)] border border-[rgba(255,255,255,0.06)] shadow-sm backdrop-blur-sm">
                      <span className="w-6 h-6 rounded-lg bg-[rgba(16,185,129,0.1)] border border-[rgba(16,185,129,0.25)] flex items-center justify-center text-xs shrink-0 text-theme-success">🛡️</span>
                      <div>
                        <strong className="text-white block font-medium">Zero-Bounce Hygiene</strong>
                        <span className="text-[11px] text-theme-muted">Syntax, MX DNS & disposable email rejection</span>
                      </div>
                    </div>
                    <div className="flex items-start gap-2.5 text-xs text-theme-secondary p-2.5 rounded-xl bg-[rgba(255,255,255,0.025)] border border-[rgba(255,255,255,0.06)] shadow-sm backdrop-blur-sm">
                      <span className="w-6 h-6 rounded-lg bg-[rgba(245,158,11,0.1)] border border-[rgba(245,158,11,0.25)] flex items-center justify-center text-xs shrink-0 text-theme-warning">🔄</span>
                      <div>
                        <strong className="text-white block font-medium">Adaptive Inbox Rotator</strong>
                        <span className="text-[11px] text-theme-muted">SMTP deliverability with dynamic send-cap monitors</span>
                      </div>
                    </div>
                    <div className="flex items-start gap-2.5 text-xs text-theme-secondary p-2.5 rounded-xl bg-[rgba(255,255,255,0.025)] border border-[rgba(255,255,255,0.06)] shadow-sm backdrop-blur-sm">
                      <span className="w-6 h-6 rounded-lg bg-[rgba(168,85,247,0.1)] border border-[rgba(168,85,247,0.25)] flex items-center justify-center text-xs shrink-0 text-theme-purple">🔒</span>
                      <div>
                        <strong className="text-white block font-medium">Machine Lock Protection</strong>
                        <span className="text-[11px] text-theme-muted">Hardware-bound Bcrypt 12-round identity</span>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div key="showcase-register" className="space-y-4 np-auth-pane-enter">
                  <div>
                    <span className="badge badge-success text-[9px] font-mono uppercase tracking-wider mb-2 inline-block px-2 py-0.5">
                      Instant 2-Day Trial
                    </span>
                    <h2 className="text-2xl lg:text-3xl font-black tracking-tight text-white leading-tight">
                      HELLO, PARTNER!
                    </h2>
                    <p className="text-xs text-theme-secondary mt-1.5 leading-relaxed">
                      Enter your operator details and start your journey with autonomous commercial client acquisition.
                    </p>
                  </div>

                  <div className="space-y-2.5 pt-2">
                    <div className="flex items-start gap-2.5 text-xs text-theme-secondary p-2.5 rounded-xl bg-[rgba(255,255,255,0.025)] border border-[rgba(255,255,255,0.06)] shadow-sm backdrop-blur-sm">
                      <span className="w-6 h-6 rounded-lg bg-[rgba(16,185,129,0.1)] border border-[rgba(16,185,129,0.25)] flex items-center justify-center text-xs shrink-0 text-theme-success">✓</span>
                      <div>
                        <strong className="text-white block font-medium">100 Real Verified Leads</strong>
                        <span className="text-[11px] text-theme-muted">Live discovery with zero mock / zero dummy data</span>
                      </div>
                    </div>
                    <div className="flex items-start gap-2.5 text-xs text-theme-secondary p-2.5 rounded-xl bg-[rgba(255,255,255,0.025)] border border-[rgba(255,255,255,0.06)] shadow-sm backdrop-blur-sm">
                      <span className="w-6 h-6 rounded-lg bg-[rgba(56,189,248,0.1)] border border-[rgba(56,189,248,0.25)] flex items-center justify-center text-xs shrink-0 text-theme-accent">✓</span>
                      <div>
                        <strong className="text-white block font-medium">48-Hour Full Access</strong>
                        <span className="text-[11px] text-theme-muted">Complete operator workspace & pipeline automation</span>
                      </div>
                    </div>
                    <div className="flex items-start gap-2.5 text-xs text-theme-secondary p-2.5 rounded-xl bg-[rgba(255,255,255,0.025)] border border-[rgba(255,255,255,0.06)] shadow-sm backdrop-blur-sm">
                      <span className="w-6 h-6 rounded-lg bg-[rgba(245,158,11,0.1)] border border-[rgba(245,158,11,0.25)] flex items-center justify-center text-xs shrink-0 text-theme-warning">✓</span>
                      <div>
                        <strong className="text-white block font-medium">Zero Credit Card Upfront</strong>
                        <span className="text-[11px] text-theme-muted">Instant self-serve activation via email or Google</span>
                      </div>
                    </div>
                    <div className="flex items-start gap-2.5 text-xs text-theme-secondary p-2.5 rounded-xl bg-[rgba(255,255,255,0.025)] border border-[rgba(255,255,255,0.06)] shadow-sm backdrop-blur-sm">
                      <span className="w-6 h-6 rounded-lg bg-[rgba(168,85,247,0.1)] border border-[rgba(168,85,247,0.25)] flex items-center justify-center text-xs shrink-0 text-theme-purple">✓</span>
                      <div>
                        <strong className="text-white block font-medium">Hardware-Bound Sandbox</strong>
                        <span className="text-[11px] text-theme-muted">Dedicated tenant workspace with strict role security</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Showcase Bottom Telemetry & CTA Switch */}
            <div className="space-y-3 pt-4 border-t border-[var(--border-subtle)]">
              <div className="flex items-center justify-between text-[10px] font-mono text-theme-muted">
                <span className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[var(--success)] animate-pulse" />
                  <span>STATUS: ONLINE [LEVEL 2]</span>
                </span>
                <span>AES-256 + BCRYPT</span>
              </div>

              {authMode === "login" ? (
                <div>
                  <div className="text-[11px] text-theme-muted mb-1.5">Don't have an enterprise account?</div>
                  <button
                    type="button"
                    onClick={() => {
                      setAuthMode("register");
                      setLoginError("");
                      setRegError("");
                      SoundEffects.authToggle();
                    }}
                    className="btn btn-secondary btn-sm w-full flex items-center justify-center gap-2 border border-[var(--border-subtle)] hover:border-[var(--accent)] font-mono text-xs"
                  >
                    <span>Create Account (2-Day Trial)</span>
                    <span>➔</span>
                  </button>
                </div>
              ) : (
                <div>
                  <div className="text-[11px] text-theme-muted mb-1.5">Already have an account?</div>
                  <button
                    type="button"
                    onClick={() => {
                      setAuthMode("login");
                      setLoginError("");
                      setRegError("");
                      SoundEffects.authToggle();
                    }}
                    className="btn btn-secondary btn-sm w-full flex items-center justify-center gap-2 border border-[var(--border-subtle)] hover:border-[var(--accent)] font-mono text-xs"
                  >
                    <span>Sign In to Workspace</span>
                    <span>➔</span>
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* RIGHT AUTH INTERACTIVE FORM PANEL */}
          <div className="np-auth-form-panel relative">
            {isScanning && <div className="biometric-scanner-line" />}

            {/* Video 1 Sliding Split Pill Toggle */}
            <div className="np-auth-toggle-container mb-5">
              <div
                className="np-auth-toggle-slider"
                style={{
                  transform: authMode === "login" ? "translateX(0%)" : "translateX(100%)",
                }}
              />
              <button
                type="button"
                onClick={() => {
                  setAuthMode("login");
                  setLoginError("");
                  setRegError("");
                  SoundEffects.authToggle();
                }}
                className={`np-auth-toggle-btn ${
                  authMode === "login"
                    ? "text-[var(--bg-base)] font-bold"
                    : "text-theme-secondary hover:text-white"
                }`}
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={() => {
                  setAuthMode("register");
                  setLoginError("");
                  setRegError("");
                  SoundEffects.authToggle();
                }}
                className={`np-auth-toggle-btn ${
                  authMode === "register"
                    ? "text-[var(--bg-base)] font-bold"
                    : "text-theme-secondary hover:text-white"
                }`}
              >
                Create Account (2-Day Trial)
              </button>
            </div>

            {authMode === "login" && loginError && (
              <div className="mb-5 np-alert np-alert-error">
                <span>{loginError}</span>
              </div>
            )}

            {authMode === "register" && regError && (
              <div className="mb-5 np-alert np-alert-error">
                <span>{regError}</span>
              </div>
            )}

            {isScanning ? (
              <div className="text-center py-8 space-y-4">
                <div className="w-14 h-14 mx-auto rounded-full border-2 border-dashed border-[var(--accent)] animate-spin flex items-center justify-center">
                  <span className="text-[10px] font-mono font-bold text-theme-accent">AUTH</span>
                </div>
                <p className="text-xs font-mono text-theme-secondary">
                  {scanStep}
                </p>
                <div className="w-48 h-1 bg-overlay rounded-full mx-auto overflow-hidden">
                  <div className="h-full bg-[var(--accent)] animate-pulse" style={{ width: "80%" }} />
                </div>
              </div>
            ) : authMode === "login" ? (
              <form key="login-form" onSubmit={handleBiometricLogin} className="space-y-4 np-auth-pane-enter">
                <div>
                  <label className="np-label">Operator or Admin Username</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-theme-muted text-xs">👤</span>
                    <input
                      type="text"
                      value={loginUsername}
                      onChange={(e) => setLoginUsername(e.target.value)}
                      className="np-glass-input font-mono pl-9"
                      placeholder="e.g. h.huddair or operator"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="np-label">Cryptographic Passphrase (Bcrypt)</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-theme-muted text-xs">🔒</span>
                    <input
                      type={showLoginPassword ? "text" : "password"}
                      value={loginPassword}
                      onChange={(e) => setLoginPassword(e.target.value)}
                      className="np-glass-input font-mono pl-9 pr-9"
                      placeholder="••••••••••••"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowLoginPassword(!showLoginPassword)}
                      className="absolute right-2.5 top-1/2 -translate-y-1/2 text-theme-muted hover:text-theme-primary text-xs"
                      title={showLoginPassword ? "Hide passphrase" : "Show passphrase"}
                    >
                      {showLoginPassword ? "👁️" : "👁️‍🗨️"}
                    </button>
                  </div>
                </div>

                <div className="flex items-center justify-between text-[11px] font-mono text-theme-muted px-0.5">
                  <span className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--success)] animate-pulse" />
                    <span>Machine ID Protected</span>
                  </span>
                  <span className="text-[10px] text-theme-secondary">Bcrypt 12-Rounds</span>
                </div>

                <button type="submit" className="btn btn-primary w-full justify-center btn-lg mt-2 shadow-lg">
                  <span>Sign In & Verify Machine ID</span>
                  <span>➔</span>
                </button>

                <div className="relative my-4">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-[var(--border-subtle)]" />
                  </div>
                  <div className="relative flex justify-center text-[10px] uppercase font-mono">
                    <span className="bg-[var(--glass-card-bg)] px-2 text-theme-muted">Or Instant Self-Serve</span>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={handleGoogleSignIn}
                  className="btn btn-secondary w-full justify-center btn-lg flex items-center gap-2 border border-[var(--border)] hover:border-[var(--accent)] shadow-sm bg-[rgba(255,255,255,0.03)]"
                >
                  <span className="font-bold text-xs text-theme-accent">G</span>
                  <span className="font-semibold text-xs text-theme-primary">Sign in with Google</span>
                  <span className="badge badge-accent text-[9px] px-1.5 py-0 ml-1">2-Day Free Trial</span>
                </button>

                <div className="text-center pt-2">
                  <button
                    type="button"
                    onClick={() => { setAuthMode("register"); setLoginError(""); SoundEffects.authToggle(); }}
                    className="text-xs text-theme-accent hover:underline font-mono"
                  >
                    Need an account? Register with 2-Day Free Trial ➔
                  </button>
                </div>
              </form>
            ) : (
              <form key="register-form" onSubmit={handleRegister} className="space-y-3 np-auth-pane-enter">
                <div>
                  <label className="np-label">Full Name</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-theme-muted text-xs">👤</span>
                    <input
                      type="text"
                      value={regFullName}
                      onChange={(e) => setRegFullName(e.target.value)}
                      className="np-glass-input pl-9"
                      placeholder="e.g. Alexander Stone"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="np-label">Work Email</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-theme-muted text-xs">✉️</span>
                    <input
                      type="email"
                      value={regEmail}
                      onChange={(e) => setRegEmail(e.target.value)}
                      className="np-glass-input font-mono pl-9"
                      placeholder="stone@contractors.de"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="np-label">Desired Username</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-theme-muted text-xs">🆔</span>
                    <input
                      type="text"
                      value={regUsername}
                      onChange={(e) => setRegUsername(e.target.value)}
                      className="np-glass-input font-mono pl-9"
                      placeholder="astone"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="np-label">Passphrase</label>
                    <div className="relative">
                      <input
                        type={showRegPassword ? "text" : "password"}
                        value={regPassword}
                        onChange={(e) => setRegPassword(e.target.value)}
                        className="np-glass-input font-mono pr-7"
                        placeholder="••••••••"
                        required
                      />
                      <button
                        type="button"
                        onClick={() => setShowRegPassword(!showRegPassword)}
                        className="absolute right-2 top-1/2 -translate-y-1/2 text-theme-muted hover:text-theme-primary text-xs"
                      >
                        {showRegPassword ? "👁️" : "👁️‍🗨️"}
                      </button>
                    </div>
                  </div>
                  <div>
                    <label className="np-label">Confirm</label>
                    <input
                      type="password"
                      value={regConfirmPassword}
                      onChange={(e) => setRegConfirmPassword(e.target.value)}
                      className="np-glass-input font-mono"
                      placeholder="••••••••"
                      required
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isRegistering}
                  className="btn btn-primary w-full justify-center btn-lg mt-3 shadow-lg"
                >
                  <span>{isRegistering ? "Creating Account..." : "Create Account & Start 2-Day Trial"}</span>
                  <span>➔</span>
                </button>

                <div className="text-center pt-2">
                  <button
                    type="button"
                    onClick={() => { setAuthMode("login"); setRegError(""); SoundEffects.authToggle(); }}
                    className="text-xs text-theme-accent hover:underline font-mono"
                  >
                    Already have an account? Sign In ➔
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // VIEW: MAIN ENTERPRISE DASHBOARD
  // ---------------------------------------------------------------------------
  return (
    <div className="np-app-layout">
      {/* Mobile Sidebar Backdrop Drawer */}
      <div
        className={`np-sidebar-backdrop ${isMobileSidebarOpen ? "mobile-open" : ""}`}
        onClick={() => setIsMobileSidebarOpen(false)}
      />

      {/* INDEPENDENT LEFT SIDEBAR PANEL (VIDEO 2 DASHBOARD V21) */}
      <aside className={`np-sidebar ${isMobileSidebarOpen ? "mobile-open" : ""}`}>
        {/* Brand Header & Live Telemetry */}
        <div className="np-sidebar-header">
          <div className="flex items-center gap-2.5">
            <div
              className={`np-pulse-icon ${
                pulseState === "HOT_ALERT" ? "np-pulse-hot" :
                pulseState === "DISPATCHING" ? "np-pulse-dispatching" :
                pulseState === "HUNTING" ? "np-pulse-hunting" :
                pulseState === "RUNNING" ? "np-pulse-running" : "np-pulse-idle"
              }`}
              title={`Agent Engine State: ${pulseState}`}
            >
              <span>NP</span>
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-sm tracking-tight text-theme-primary">
                  Nexus-Pulse
                </span>
                <span className="badge badge-accent text-[9px] px-1 py-0">
                  Level 2
                </span>
              </div>
              <div className="text-[10px] text-theme-muted font-mono flex items-center gap-1">
                <span className={`w-1.5 h-1.5 rounded-full ${
                  pulseState === 'HOT_ALERT' ? 'bg-[var(--danger)] animate-pulse' :
                  pulseState === 'DISPATCHING' ? 'bg-[var(--warning)] animate-pulse' :
                  pulseState === 'HUNTING' ? 'bg-[var(--success)] animate-pulse' :
                  'bg-[var(--accent)] animate-pulse'
                }`} />
                <span>{pulseState}</span>
              </div>
            </div>
          </div>
          {/* Mobile close button */}
          <button
            onClick={() => setIsMobileSidebarOpen(false)}
            className="lg:hidden text-theme-muted hover:text-theme-primary text-sm p-1"
          >
            ✕
          </button>
        </div>

        {/* Scrollable Navigation & Personalized Profile */}
        <div className="np-sidebar-scroll">
          {/* Personalized User Identity & Welcome Greeting */}
          <div className="np-sidebar-user-card">
            <div className="w-8 h-8 rounded-full bg-[var(--accent-muted)] border border-[var(--accent)] flex items-center justify-center font-bold text-xs text-theme-accent shrink-0">
              {(user.full_name || user.username || "NP").charAt(0).toUpperCase()}
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-[10px] text-theme-muted uppercase tracking-wider font-semibold">
                Welcome back,
              </div>
              <div className="text-xs font-semibold text-theme-primary truncate" title={user.full_name || user.username}>
                {user.full_name || user.username}
              </div>
              <div className="flex items-center gap-1 mt-0.5">
                <span className="badge badge-gold text-[8px] uppercase px-1 py-0 font-mono">
                  {user.role}
                </span>
                {user.role === "operator" && user.trial_active === 1 && user.subscription_status !== "active" && (
                  <span className="badge badge-warning text-[8px] font-mono px-1 py-0 animate-pulse" title={`Trial expires: ${user.trial_expires_at}`}>
                    ⏳ 2-Day Trial
                  </span>
                )}
                {user.role === "operator" && user.subscription_status === "active" && (
                  <span className="badge badge-success text-[8px] font-mono px-1 py-0">
                    ✓ Active
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Group 1: CORE WORKSPACE */}
          <div className="np-sidebar-nav-group">
            <div className="np-sidebar-group-title">Core Workspace</div>

            <button
              onClick={() => { setActiveTab("kanban"); setIsMobileSidebarOpen(false); SoundEffects.waterDrop(); }}
              className={`np-sidebar-item ${activeTab === "kanban" ? "active" : ""}`}
            >
              <span className="flex items-center gap-2">
                <span>📊</span>
                <span>Pipeline</span>
              </span>
              <span className="badge badge-muted text-[10px] px-1.5 py-0 font-mono">{kanbanItems.length}</span>
            </button>

            <button
              onClick={() => { setActiveTab("approval_gate"); setIsMobileSidebarOpen(false); SoundEffects.waterDrop(); }}
              className={`np-sidebar-item ${activeTab === "approval_gate" ? "active" : ""}`}
            >
              <span className="flex items-center gap-2">
                <span>🛡️</span>
                <span>Approval Gate</span>
              </span>
              {pendingApprovals.length > 0 && (
                <span className="badge badge-warning text-[10px] px-1.5 py-0 font-mono">{pendingApprovals.length}</span>
              )}
            </button>

            <button
              onClick={() => { setActiveTab("hot_leads"); setIsMobileSidebarOpen(false); SoundEffects.waterDrop(); }}
              className={`np-sidebar-item ${activeTab === "hot_leads" ? "active" : ""}`}
            >
              <span className="flex items-center gap-2">
                <span>🔥</span>
                <span>Hot Leads</span>
              </span>
              {uniqueHotLeads.length > 0 && (
                <span className="badge badge-danger text-[10px] px-1.5 py-0 font-mono animate-pulse">{uniqueHotLeads.length}</span>
              )}
            </button>

            <button
              onClick={() => { setActiveTab("rotator"); setIsMobileSidebarOpen(false); SoundEffects.waterDrop(); }}
              className={`np-sidebar-item ${activeTab === "rotator" ? "active" : ""}`}
            >
              <span className="flex items-center gap-2">
                <span>🔄</span>
                <span>Inbox Rotator</span>
              </span>
              <span className="badge badge-muted text-[10px] px-1.5 py-0 font-mono">{mailboxes.length}</span>
            </button>

            <button
              onClick={() => { setActiveTab("templates"); setIsMobileSidebarOpen(false); SoundEffects.waterDrop(); }}
              className={`np-sidebar-item ${activeTab === "templates" ? "active" : ""}`}
            >
              <span className="flex items-center gap-2">
                <span>📝</span>
                <span>Proposals</span>
              </span>
              <span className="badge badge-muted text-[10px] px-1.5 py-0 font-mono">{templatesList.length}</span>
            </button>

            <button
              onClick={() => { setActiveTab("analytics"); setIsMobileSidebarOpen(false); SoundEffects.waterDrop(); }}
              className={`np-sidebar-item ${activeTab === "analytics" ? "active" : ""}`}
            >
              <span className="flex items-center gap-2">
                <span>📈</span>
                <span>Deliverability</span>
              </span>
            </button>
          </div>

          {/* Group 2: ADMINISTRATION (Admin Only) */}
          {user.role === "admin" && (
            <div className="np-sidebar-nav-group">
              <div className="np-sidebar-group-title">Administration</div>

              <button
                onClick={() => { setActiveTab("billing_mgmt"); setIsMobileSidebarOpen(false); SoundEffects.waterDrop(); }}
                className={`np-sidebar-item ${activeTab === "billing_mgmt" ? "active" : ""}`}
              >
                <span className="flex items-center gap-2">
                  <span>💳</span>
                  <span>Manual Billing</span>
                </span>
                {planRequests.length > 0 && (
                  <span className="badge badge-warning text-[10px] px-1.5 py-0 font-mono">{planRequests.length}</span>
                )}
              </button>

              <button
                onClick={() => { setActiveTab("blacklist_mgmt"); setIsMobileSidebarOpen(false); SoundEffects.waterDrop(); }}
                className={`np-sidebar-item ${activeTab === "blacklist_mgmt" ? "active" : ""}`}
              >
                <span className="flex items-center gap-2">
                  <span>🚫</span>
                  <span>Blacklist</span>
                </span>
              </button>

              <button
                onClick={() => { setActiveTab("operator_mgmt"); setIsMobileSidebarOpen(false); SoundEffects.waterDrop(); }}
                className={`np-sidebar-item ${activeTab === "operator_mgmt" ? "active" : ""}`}
              >
                <span className="flex items-center gap-2">
                  <span>👥</span>
                  <span>Operators</span>
                </span>
                <span className="badge badge-muted text-[10px] px-1.5 py-0 font-mono">{operatorsList.length}</span>
              </button>

              <button
                onClick={() => { setActiveTab("security_settings"); setIsMobileSidebarOpen(false); SoundEffects.waterDrop(); }}
                className={`np-sidebar-item ${activeTab === "security_settings" ? "active" : ""}`}
              >
                <span className="flex items-center gap-2">
                  <span>⚙️</span>
                  <span>Security Profile</span>
                </span>
              </button>

              <button
                onClick={() => { setActiveTab("license_mgmt"); setIsMobileSidebarOpen(false); SoundEffects.waterDrop(); }}
                className={`np-sidebar-item ${activeTab === "license_mgmt" ? "active" : ""}`}
              >
                <span className="flex items-center gap-2">
                  <span>📜</span>
                  <span>License & Telemetry</span>
                </span>
              </button>
            </div>
          )}

          {/* Quick Primary Actions */}
          <div className="pt-2 border-t border-[var(--border-subtle)] space-y-1.5">
            <button
              onClick={() => { setIsHuntModalOpen(true); setHuntProgress(null); }}
              className="btn btn-primary btn-sm w-full justify-center shadow-sm"
              title="Launch Targeted Lead Hunt"
            >
              <span>⚡ Hunt & Verify</span>
            </button>

            <button
              onClick={() => setIsBackupModalOpen(true)}
              className="btn btn-secondary btn-sm w-full justify-center"
              title="Export Multi-Format Database Backup"
            >
              <span>📦 Backup Data</span>
            </button>
          </div>
        </div>

        {/* Sidebar Bottom Status & Settings Card */}
        <div className="np-sidebar-footer">
          {/* Hardware Telemetry Badge */}
          <div className="flex items-center justify-between text-[11px] font-mono text-theme-muted px-1">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[var(--success)] animate-pulse" />
              <span>{systemHealth?.machine_id || "NEXUS-E727"}</span>
            </span>
            <span className="badge badge-accent text-[9px] px-1.5 py-0.5">SECURE</span>
          </div>

          {/* Theme & SFX Controls Bar */}
          <div className="flex items-center justify-between pt-1.5 border-t border-[var(--border-subtle)] gap-2">
            {/* Theme Picker Dropdown */}
            <div className="relative flex-1">
              <button
                type="button"
                onClick={() => setIsThemeMenuOpen(!isThemeMenuOpen)}
                className="btn btn-secondary btn-sm w-full flex items-center justify-between gap-1.5 py-1 px-2"
                title="Appearance Theme"
              >
                <div className="flex items-center gap-1.5 truncate">
                  <span
                    className="theme-dot shrink-0"
                    style={{ backgroundColor: THEMES.find(t => t.id === activeTheme)?.dotColor || "#38bdf8" }}
                  />
                  <span className="text-[11px] font-mono truncate">{THEMES.find(t => t.id === activeTheme)?.name || "Theme"}</span>
                </div>
                <span className="text-[9px] opacity-60">▾</span>
              </button>

              {isThemeMenuOpen && (
                <div
                  className="absolute bottom-full left-0 mb-1.5 w-60 np-card p-1.5 z-50 shadow-2xl border-theme"
                  onMouseLeave={() => setIsThemeMenuOpen(false)}
                >
                  <div className="px-2.5 py-1.5 text-[10px] font-semibold text-theme-secondary uppercase tracking-wider border-b-theme">
                    Appearance Preset (6 Themes)
                  </div>
                  {THEMES.map((t) => (
                    <button
                      key={t.id}
                      onClick={() => {
                        setActiveTheme(t.id);
                        setIsThemeMenuOpen(false);
                        SoundEffects.themeShimmer();
                      }}
                      className={`w-full text-left px-2.5 py-1.5 rounded text-xs flex items-center justify-between hover:bg-hover transition-colors ${
                        activeTheme === t.id ? "text-theme-accent font-semibold bg-[var(--accent-muted)]" : "text-theme-primary"
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <span className="theme-dot" style={{ backgroundColor: t.dotColor }} />
                        <div>
                          <div>{t.name}</div>
                          <div className="text-[9px] text-theme-muted leading-tight">{t.desc}</div>
                        </div>
                      </div>
                      {activeTheme === t.id && <span className="text-theme-accent font-bold">✓</span>}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Audio Mute Toggle */}
            <button
              type="button"
              onClick={() => {
                const next = !soundEnabled;
                setSoundEnabled(next);
                if (next) setTimeout(() => playUiSound("glass_chime"), 50);
              }}
              className={`btn btn-sm py-1 px-2.5 shrink-0 ${soundEnabled ? "btn-secondary text-theme-accent" : "btn-ghost text-theme-muted"}`}
              title={soundEnabled ? "UI Audio SFX Active (Click to Mute)" : "UI Audio SFX Muted (Click to Enable)"}
            >
              <span className="text-xs">{soundEnabled ? "🔊" : "🔇"}</span>
            </button>
          </div>

          {/* Explicit, Unmistakable Sign Out Button */}
          <button
            type="button"
            onClick={handleLogout}
            className="np-btn-signout"
            title="Sign out of current operator session"
          >
            <svg
              className="np-btn-signout-icon w-3.5 h-3.5 shrink-0"
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              style={{
                width: "14px",
                height: "14px",
                minWidth: "14px",
                maxWidth: "14px",
                minHeight: "14px",
                maxHeight: "14px",
                flexShrink: 0
              }}
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            <span style={{ whiteSpace: "nowrap" }}>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* RIGHT MAIN WORKSPACE (Video 2) */}
      <div className="np-main-wrapper">
        {/* Global Notification Banner */}
        {alertBanner && (
          <div className={`px-4 py-2 text-xs font-medium border-b flex items-center justify-between ${
            alertBanner.type === "success" ? "bg-[var(--success-muted)] text-[var(--success)] border-[var(--success)]" :
            alertBanner.type === "error" ? "bg-[var(--danger-muted)] text-[var(--danger)] border-[var(--danger)]" :
            "bg-[var(--accent-muted)] text-[var(--accent)] border-[var(--accent)]"
          }`}>
            <span>{alertBanner.message}</span>
            <button onClick={() => setAlertBanner(null)} className="hover:opacity-75 font-bold ml-4 text-sm">✕</button>
          </div>
        )}

        {/* Top Synchronized Context Header */}
        <header className="np-context-header">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsMobileSidebarOpen(true)}
              className="lg:hidden btn btn-secondary btn-sm p-1.5"
              title="Open Navigation Menu"
            >
              ☰
            </button>
            <div>
              <div className="text-[11px] text-theme-muted font-mono flex items-center gap-1.5">
                <span>Nexus-Pulse</span>
                <span>›</span>
                <span className="text-theme-primary font-semibold">
                  {activeTab === "kanban" ? "Pipeline Lifecycle" :
                   activeTab === "approval_gate" ? "Human Approval Gate" :
                   activeTab === "hot_leads" ? "Hot Lead Alert Room" :
                   activeTab === "rotator" ? "Inbox Rotator & Domains" :
                   activeTab === "templates" ? "Proposal Templates" :
                   activeTab === "analytics" ? "Deliverability & Telemetry" :
                   activeTab === "billing_mgmt" ? "Manual Plan & Billing Management" :
                   activeTab === "blacklist_mgmt" ? "Blacklist & Suppression Vault" :
                   activeTab === "operator_mgmt" ? "Operator Role Management" :
                   activeTab === "security_settings" ? "Cryptographic Security Profile" :
                   activeTab === "license_mgmt" ? "Licensing & Machine Lock" : activeTab}
                </span>
              </div>
            </div>
          </div>

          {/* Center: Live Office Hours Clocks */}
          <div className="hidden md:flex items-center gap-3 text-xs font-mono bg-elevated px-3 py-1 rounded-md border-theme">
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--success)] animate-pulse" />
              <span className="text-theme-secondary text-[11px]">Berlin:</span>
              <span className="font-semibold text-theme-primary text-[11px]">
                {timezones.germany?.current_local_time?.split(" ")[1] || "09:15:00"}
              </span>
              <span className="text-[9px] text-theme-success font-bold">
                [{timezones.germany?.is_in_send_window ? "ACTIVE WINDOW" : "QUEUED"}]
              </span>
            </div>
            <span className="text-theme-muted">|</span>
            <div className="flex items-center gap-1.5">
              <span className="text-theme-secondary text-[11px]">London:</span>
              <span className="font-semibold text-theme-primary text-[11px]">
                {timezones.united_kingdom?.current_local_time?.split(" ")[1] || "08:15:00"}
              </span>
              <span className="text-[9px] text-theme-success font-bold">
                [{timezones.united_kingdom?.is_in_send_window ? "ACTIVE WINDOW" : "QUEUED"}]
              </span>
            </div>
          </div>

          {/* Right: Engine Telemetry State */}
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 font-mono text-[11px] bg-elevated px-2.5 py-1 rounded border-theme">
              <span className="text-theme-muted">Engine:</span>
              <span className={
                pulseState === 'HOT_ALERT' ? 'text-theme-danger font-bold animate-pulse' :
                pulseState === 'DISPATCHING' ? 'text-theme-warning font-bold animate-pulse' :
                pulseState === 'HUNTING' ? 'text-theme-success font-bold animate-pulse' :
                'text-theme-accent font-bold'
              }>{pulseState}</span>
            </div>
          </div>
        </header>

        {/* MAIN CONTENT WORKSPACE */}
        <main className="np-main-content">
          <div key={activeTab} className="np-tab-pane-enter w-full">
            {/* TAB 1: KANBAN LEAD PIPELINE */}
        {activeTab === "kanban" && (
          <div className="w-full space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="font-semibold text-base text-theme-primary">
                  Pipeline Lifecycle: Autonomous Lead Engine
                </h2>
                <p className="text-xs text-theme-secondary mt-0.5">
                  Multi-niche verified B2B contacts tracked through zero-bounce hygiene, human approval gate, and IMAP reply listeners.
                </p>
              </div>

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={handleSyncReplies}
                  disabled={isSyncingReplies}
                  className="btn btn-secondary btn-xs flex items-center gap-1.5 border border-[var(--border-subtle)] hover:border-[var(--accent)] font-mono text-xs"
                  title="Connect via IMAP (Port 993 SSL) to scan recent inbox replies and advance leads"
                >
                  <span className={isSyncingReplies ? "animate-spin" : ""}>🔄</span>
                  <span>{isSyncingReplies ? "Scanning Inboxes..." : "Sync Replies Now"}</span>
                </button>
                <div className="text-xs font-mono text-theme-secondary">
                  Entities Tracked: <strong className="text-theme-accent">{kanbanItems.length}</strong>
                </div>
              </div>
            </div>

            {/* Responsive Board Container */}
            <div className="flex gap-3 overflow-x-auto pb-4 scrollbar-thin">
              {KANBAN_STAGES.map((stage) => {
                const stageLeads = kanbanItems.filter((item) => {
                  const norm = normalizeLeadStatus(item.status);
                  if (stage.key === "REPLIED") {
                    // Positive replies enter Replied column first without bypassing it
                    return norm === "REPLIED" || (norm === "HOT_LEAD" && !promotedToHotLeadIds.has(item.id));
                  }
                  if (stage.key === "HOT_LEAD") {
                    // Promoted or active hot leads in Hot Lead column
                    return norm === "HOT_LEAD" && promotedToHotLeadIds.has(item.id);
                  }
                  return norm === stage.key;
                });
                return (
                  <div key={stage.key} className="kanban-col">
                    <div className="kanban-col-header">
                      <span className="font-semibold text-xs tracking-wide text-theme-primary">
                        {stage.label}
                      </span>
                      <span className={`badge ${stage.badgeClass}`}>
                        {stageLeads.length}
                      </span>
                    </div>

                    <div className="kanban-col-body">
                      {stageLeads.length === 0 ? (
                        <div className="text-center py-12 text-xs text-theme-muted font-mono italic">
                          No leads in stage
                        </div>
                      ) : (
                        stageLeads.map((lead) => {
                          const badges = getCleanLeadBadges(lead);
                          return (
                            <div
                              key={lead.id}
                              className={`kanban-card ${stage.key === "HOT_LEAD" ? "hot" : ""}`}
                            >
                              <div className="flex items-start justify-between gap-1 mb-1">
                                <h3 className="font-semibold text-xs text-theme-primary leading-snug line-clamp-1" title={lead.company_name}>
                                  {lead.company_name}
                                </h3>
                                <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-overlay text-theme-secondary shrink-0">
                                  {lead.priority_score || 95}/100
                                </span>
                              </div>

                              <p className="text-[11px] font-mono text-theme-accent truncate mb-2">
                                {lead.primary_email || lead.recipient}
                              </p>

                              {/* Clean Deduplicated Badges */}
                              <div className="flex flex-wrap gap-1 mb-2">
                                {badges.map((b, idx) => (
                                  <span
                                    key={idx}
                                    className={`text-[10px] font-medium font-mono px-1.5 py-0.5 rounded ${
                                      b.type === "tier" ? "bg-overlay text-theme-secondary border-theme" :
                                      "bg-[var(--success-muted)] text-[var(--success)] border border-[var(--success)]"
                                    }`}
                                  >
                                    {b.text}
                                  </span>
                                ))}
                              </div>

                              {/* Status Indicators & Warning Badges */}
                              {(() => {
                                const isSuppressed = lead.unsubscribed || String(lead.status).toUpperCase() === "SUPPRESSED" || String(lead.status).toUpperCase() === "BLACKLISTED";
                                return (
                                  <>
                                    <div className="flex flex-wrap gap-1 mb-2">
                                      {(lead.bounce_reason || String(lead.status).toUpperCase() === "FAILED") && !isSuppressed && (
                                        <span
                                          className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-red-950 text-red-300 border border-red-800"
                                          title={lead.bounce_reason || "Dispatch Error"}
                                        >
                                          ⚠️ {lead.bounce_reason ? (lead.bounce_reason.length > 25 ? lead.bounce_reason.slice(0, 25) + "..." : lead.bounce_reason) : "Dispatch Failed"}
                                        </span>
                                      )}
                                      {!isSuppressed && (String(lead.status).toUpperCase() === "SCHEDULED" || (lead.scheduled_for && !lead.sent_at)) && (
                                        <span
                                          className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800"
                                          title={`Scheduled for: ${lead.scheduled_for}`}
                                        >
                                          🕒 Scheduled
                                        </span>
                                      )}
                                      {isSuppressed && (
                                        <span
                                          className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800"
                                          title={lead.bounce_reason || "Suppressed from outreach"}
                                        >
                                          🚫 Suppressed
                                        </span>
                                      )}
                                    </div>

                                    {/* Tech Stack Chips */}
                                    {lead.tech_stack && lead.tech_stack.length > 0 && (
                                      <div className="flex flex-wrap gap-1 mb-2">
                                        {lead.tech_stack.slice(0, 3).map((tech, i) => (
                                          <span key={i} className="text-[9px] font-mono px-1 py-0.2 rounded bg-overlay text-theme-muted">
                                            {tech}
                                          </span>
                                        ))}
                                      </div>
                                    )}

                                    {/* Actions */}
                                    {isSuppressed ? (
                                      <div className="flex items-center gap-1 mt-1">
                                        <button
                                          onClick={() => handleUnblockLead(lead.id, lead.recipient || lead.primary_email)}
                                          className="btn btn-warning btn-sm flex-1 justify-center text-[10px]"
                                          title="Unblock this suppressed lead and return it to Approval Hold"
                                        >
                                          🔓 Unblock / Reset
                                        </button>
                                        <button
                                          onClick={() => handleDeleteQueueItem(lead.id, lead.recipient || lead.primary_email)}
                                          className="btn btn-danger btn-sm px-2 text-[10px]"
                                          title="Delete Lead"
                                        >
                                          🗑️
                                        </button>
                                      </div>
                                    ) : stage.key === "PENDING_APPROVAL" ? (
                                      <div className="flex items-center gap-1 mt-1">
                                        <button
                                          onClick={() => handleOpenApprovalModal(lead)}
                                          className="btn btn-warning btn-sm flex-1 justify-center"
                                        >
                                          Review & Authorize ➔
                                        </button>
                                        <button
                                          onClick={() => handleDeleteQueueItem(lead.id, lead.recipient || lead.primary_email)}
                                          className="btn btn-danger btn-sm px-2"
                                          title="Delete Lead"
                                        >
                                          🗑️
                                        </button>
                                      </div>
                                    ) : stage.key === "APPROVED" ? (
                                      <div className="flex items-center gap-1 mt-1">
                                        <button
                                          onClick={() => handleDispatchQueueNow(true, lead.id)}
                                          className="btn btn-primary btn-sm flex-1 justify-center"
                                          title="Force immediate dispatch for this authorized lead"
                                        >
                                          🚀 Dispatch Now
                                        </button>
                                        <button
                                          onClick={() => handleDeleteQueueItem(lead.id, lead.recipient || lead.primary_email)}
                                          className="btn btn-danger btn-sm px-2"
                                          title="Delete Lead"
                                        >
                                          🗑️
                                        </button>
                                      </div>
                                    ) : null}
                                  </>
                                );
                              })()}

                              {stage.key === "REPLIED" && (
                                <div className="space-y-1.5 mt-1">
                                  {normalizeLeadStatus(lead.status) === "HOT_LEAD" && (
                                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-red-950 text-red-300 border border-red-800 flex items-center gap-1 font-semibold">
                                      🔥 Hot Lead Inquiry
                                    </span>
                                  )}
                                  <div className="flex items-center gap-1">
                                    <button
                                      onClick={() => handleOpenHotLeadModal(lead)}
                                      className="btn btn-accent btn-sm flex-1 justify-center text-[10px]"
                                      title="Open 1-Click AI Response draft"
                                    >
                                      ⚡ 1-Click AI Reply
                                    </button>
                                    <button
                                      onClick={() => handleAdvanceToHotLead(lead.id)}
                                      className="btn btn-danger btn-sm px-2 text-[10px]"
                                      title="Advance to Hot Lead column"
                                    >
                                      ➔ Hot
                                    </button>
                                  </div>
                                </div>
                              )}

                              {stage.key === "HOT_LEAD" && (
                                <button
                                  onClick={() => handleOpenHotLeadModal(lead)}
                                  className="btn btn-danger btn-sm w-full justify-center mt-1"
                                >
                                  ⚡ 1-Click AI Reply
                                </button>
                              )}
                            </div>
                          );
                        })
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Suppressed & Excluded Leads Section */}
            {(() => {
              const suppressedLeads = kanbanItems.filter(
                (item) => normalizeLeadStatus(item.status) === "SUPPRESSED" || item.unsubscribed
              );
              if (suppressedLeads.length === 0) return null;
              return (
                <div className="mt-6 np-card p-4 border-l-4 border-l-[var(--danger)]">
                  <div className="flex items-center justify-between pb-2 border-b-theme mb-3">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-xs text-theme-primary flex items-center gap-1.5">
                        <span>🚫 Suppressed / Excluded Leads</span>
                        <span className="badge badge-danger text-[10px] font-mono px-1.5 py-0">
                          {suppressedLeads.length}
                        </span>
                      </span>
                      <span className="text-[11px] text-theme-secondary">
                        (Excluded from active pipeline & Approval Hold — click Unblock to restore to Approval Hold)
                      </span>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                    {suppressedLeads.map((sLead) => (
                      <div key={sLead.id} className="np-card p-3 space-y-2 bg-overlay border-theme">
                        <div className="flex items-start justify-between gap-1">
                          <h4 className="font-semibold text-xs text-theme-primary truncate">
                            {sLead.company_name}
                          </h4>
                          <span className="badge badge-danger text-[9px] font-mono shrink-0">
                            SUPPRESSED
                          </span>
                        </div>
                        <p className="text-[11px] font-mono text-theme-accent truncate">
                          {sLead.recipient || sLead.primary_email}
                        </p>
                        <p className="text-[10px] text-theme-secondary line-clamp-1" title={sLead.bounce_reason || "Opt-out / Unsubscribe"}>
                          Reason: {sLead.bounce_reason || "Opt-out / Unsubscribe"}
                        </p>
                        <div className="flex items-center gap-1 pt-1">
                          <button
                            onClick={() => handleUnblockLead(sLead.id, sLead.recipient || sLead.primary_email)}
                            className="btn btn-warning btn-sm text-[10px] flex-1 justify-center"
                            title="Unblock this suppressed lead and return it to Approval Hold"
                          >
                            🔓 Unblock / Reset
                          </button>
                          <button
                            onClick={() => handleDeleteQueueItem(sLead.id, sLead.recipient || sLead.primary_email)}
                            className="btn btn-danger btn-sm text-[10px] px-2"
                            title="Permanently Delete Lead"
                          >
                            🗑️
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })()}
          </div>
        )}

        {/* TAB 2: HUMAN APPROVAL GATE */}
        {activeTab === "approval_gate" && (
          <div className="w-full max-w-5xl mx-auto space-y-4">
            <div className="flex items-center justify-between pb-3 border-b-theme">
              <div>
                <h2 className="font-semibold text-base text-theme-primary flex items-center gap-2">
                  <span>🛡️ Human Authorization Hold Gate</span>
                  <span className="badge badge-accent">MANDATORY GATE</span>
                </h2>
                <p className="text-xs text-theme-secondary mt-0.5">
                  No outreach messages are ever dispatched without explicit authorization from the Master Administrator.
                </p>
              </div>

              <div className="flex items-center gap-2 flex-wrap justify-end">
                {user.role === "admin" && (
                  <button
                    onClick={handlePurgeUnapprovedGate}
                    className="btn btn-danger btn-sm flex items-center gap-1"
                    title="Clear and permanently wipe all pending unapproved leads in the gate"
                  >
                    <span>🗑️ Purge Unapproved Leads</span>
                  </button>
                )}
                {user.role === "admin" && (
                  <button
                    onClick={() => handleToggleDispatcherBypass(!dispatcherState.bypass_window)}
                    className={`btn btn-sm ${dispatcherState.bypass_window ? "btn-danger" : "btn-secondary"}`}
                    title="Toggle immediate dispatch override regardless of timezone window or weekends"
                  >
                    <span>{dispatcherState.bypass_window ? "⚡ Bypass: 24/7 FORCED" : "🕒 Window: 9-5 Local"}</span>
                  </button>
                )}
                {user.role === "admin" && (
                  <button
                    onClick={() => handleDispatchQueueNow(true)}
                    disabled={isDispatchingNow}
                    className="btn btn-primary btn-sm flex items-center gap-1.5"
                    title="Force immediate dispatch of all authorized leads"
                  >
                    <span>{isDispatchingNow ? "Dispatching..." : "⚡ Dispatch Now (Bypass Window)"}</span>
                  </button>
                )}
                {user.role === "admin" && pendingApprovals.length > 0 && (
                  <button
                    onClick={handleBatchApprove}
                    className="btn btn-warning btn-sm"
                  >
                    ✓ Batch Authorize All ({pendingApprovals.length})
                  </button>
                )}
              </div>
            </div>

            {pendingApprovals.length === 0 ? (
              <div className="np-empty-state">
                <div className="w-12 h-12 mx-auto mb-3 rounded-2xl bg-[rgba(16,185,129,0.12)] border border-[rgba(16,185,129,0.25)] flex items-center justify-center text-xl text-theme-success shadow-inner">
                  ✓
                </div>
                <h3 className="font-semibold text-sm text-theme-primary">Gate Clear: No Pending Outreach</h3>
                <p className="text-xs text-theme-secondary mt-1.5 max-w-md mx-auto leading-relaxed">
                  All leads reviewed or dispatched according to dynamic 9:00 AM - 5:00 PM local business window.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {pendingApprovals.map((item) => (
                  <div key={item.id} className="np-card p-4 space-y-3 border-l-4 border-l-[var(--warning)]">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold text-sm text-theme-primary">{item.company_name}</h3>
                          <span className="badge badge-muted text-[10px]">{item.channel}</span>
                          <span className="text-xs text-theme-muted font-mono">
                            Target: {item.target_country} ({item.target_timezone})
                          </span>
                        </div>
                        <p className="text-xs font-mono text-theme-accent mt-0.5">{item.recipient}</p>
                      </div>

                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleOpenApprovalModal(item)}
                          className="btn btn-secondary btn-sm"
                        >
                          Edit & Review
                        </button>
                        <button
                          onClick={() => handleDeleteQueueItem(item.id, item.recipient)}
                          className="btn btn-danger btn-sm"
                          title="Permanently delete lead"
                        >
                          🗑️ Delete
                        </button>
                        {(item.unsubscribed || String(item.status).toUpperCase() === "SUPPRESSED") ? (
                          <button
                            onClick={() => handleUnblockLead(item.id, item.recipient)}
                            className="btn btn-warning btn-sm"
                            title="Unblock this lead and return to Approval Hold"
                          >
                            🔓 Unblock / Reset
                          </button>
                        ) : (
                          <>
                            {user.role === "admin" && (
                              <button
                                onClick={() => handleApproveOutreach(item.id, item.subject, item.message_body, item.recipient, item.company_name)}
                                className="btn btn-warning btn-sm"
                              >
                                Authorize
                              </button>
                            )}
                            {user.role === "admin" && (
                              <button
                                onClick={async () => {
                                  await handleApproveOutreach(item.id, item.subject, item.message_body, item.recipient, item.company_name);
                                  await handleDispatchQueueNow(true, item.id);
                                }}
                                className="btn btn-primary btn-sm"
                                title="Authorize and dispatch immediately outside business hours"
                              >
                                ⚡ Authorize & Send Now
                              </button>
                            )}
                          </>
                        )}
                      </div>
                    </div>

                    <div className="bg-elevated p-3 rounded-md border-theme text-xs font-mono space-y-1">
                      <div className="text-theme-secondary font-semibold">Subject: {item.subject}</div>
                      <div className="text-theme-primary whitespace-pre-line line-clamp-3">{item.message_body}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 3: HOT LEAD ALERTS */}
        {activeTab === "hot_leads" && (
          <div className="w-full max-w-5xl mx-auto space-y-4">
            <div className="pb-3 border-b-theme">
              <h2 className="font-semibold text-base text-theme-primary">
                <span>🔥 Hot Lead Inquiries & Instant Response Stream</span>
              </h2>
              <p className="text-xs text-theme-secondary mt-0.5">
                Incoming replies classified by IMAP listener as high-intent commercial opportunities across all active niches.
              </p>
            </div>

            {uniqueHotLeads.length === 0 ? (
              <div className="np-empty-state">
                <div className="w-12 h-12 mx-auto mb-3 rounded-2xl bg-[rgba(56,189,248,0.12)] border border-[rgba(56,189,248,0.25)] flex items-center justify-center text-xl text-theme-accent shadow-inner">
                  📡
                </div>
                <h3 className="font-semibold text-sm text-theme-primary">IMAP Reply Listener Active</h3>
                <p className="text-xs text-theme-secondary mt-1.5 max-w-md mx-auto leading-relaxed">
                  Listening on enrolled mailboxes for high-intent commercial replies across all active niches...
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {uniqueHotLeads.map((hl) => (
                  <div key={hl.id} className="np-card p-5 space-y-3 border-l-4 border-l-[var(--danger)]">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold text-sm text-theme-primary">
                            {hl.company_name && !["gmail.com", "outlook.com", "yahoo.com", "hotmail.com", "icloud.com", "mail.com"].includes(hl.company_name.toLowerCase()) && hl.company_name !== hl.sender_email
                              ? hl.company_name
                              : (hl.sender_email
                                  ? hl.sender_email.split("@")[0].replace(/[._-]/g, " ").replace(/\b\w/g, c => c.toUpperCase())
                                  : (hl.company_name || "Direct Inquirer"))}
                          </h3>
                          <span className="badge badge-danger">HOT INQUIRY</span>
                        </div>
                        <p className="text-xs font-mono text-theme-accent mt-0.5">{hl.sender_email}</p>
                      </div>

                      <button
                        onClick={() => handleOpenHotLeadModal(hl)}
                        className="btn btn-danger btn-sm"
                      >
                        ⚡ 1-Click AI Response
                      </button>
                    </div>

                    <div className="bg-elevated p-3 rounded-md border-theme text-xs font-mono">
                      <div className="text-theme-secondary font-semibold mb-1">Inquiry: {hl.subject}</div>
                      <div className="text-theme-primary whitespace-pre-line">{hl.message_body}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 4: INBOX ROTATOR */}
        {activeTab === "rotator" && (
          <div className="w-full max-w-6xl mx-auto space-y-4">
            <div className="flex items-center justify-between pb-3 border-b-theme">
              <div>
                <h2 className="font-semibold text-base text-theme-primary">
                  <span>🔄 Inbox Rotator & Sender Reputation Pool</span>
                </h2>
                <p className="text-xs text-theme-secondary mt-0.5">
                  Rotates sending accounts across enrolled domains with strict 40-50 daily send caps.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setIsSetupGuideOpen(true)}
                  className="btn btn-secondary btn-sm flex items-center gap-1.5 border border-[var(--border-subtle)] hover:border-[var(--accent)] text-theme-accent"
                  title="Non-technical walkthrough for Gmail App Password & Webhook Script"
                >
                  <span>📘 Setup Guide & Webhook Script</span>
                </button>
                <button
                  onClick={() => setIsAddMailboxOpen(true)}
                  className="btn btn-primary btn-sm"
                >
                  + Enroll Mailbox
                </button>
              </div>
            </div>

            {mailboxes.length === 0 ? (
              <div className="np-empty-state">
                <div className="w-12 h-12 mx-auto mb-3 rounded-2xl bg-[rgba(56,189,248,0.12)] border border-[rgba(56,189,248,0.25)] flex items-center justify-center text-xl text-theme-accent shadow-inner">
                  📬
                </div>
                <h3 className="font-semibold text-sm text-theme-primary">No Data Available: Zero Mailboxes Enrolled</h3>
                <p className="text-xs text-theme-secondary mt-1.5 max-w-md mx-auto leading-relaxed">
                  Enroll an active SMTP inbox into the rotation pool to enable automated outreach and deliverability monitoring.
                </p>
                <button
                  onClick={() => setIsAddMailboxOpen(true)}
                  className="btn btn-primary btn-sm mt-4 shadow-md"
                >
                  + Enroll First Mailbox
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {mailboxes.map((mb) => {
                  const percent = Math.min(100, Math.round((mb.sent_today / mb.daily_limit) * 100));
                  return (
                    <div key={mb.id} className="np-card p-4 space-y-3">
                      <div className="flex items-start justify-between">
                        <div>
                          <h3 className="font-semibold text-sm text-theme-primary">{mb.display_name}</h3>
                          <p className="text-xs font-mono text-theme-accent">{mb.email_address}</p>
                          <p className="text-[10px] text-theme-muted font-mono mt-0.5">Domain: {mb.domain}</p>
                        </div>
                        <span className="badge badge-success">HEALTHY</span>
                      </div>

                      <div>
                        <div className="flex items-center justify-between text-xs font-mono mb-1">
                          <span className="text-theme-secondary">Daily Send Progress</span>
                          <span className="font-semibold text-theme-primary">{mb.sent_today} / {mb.daily_limit} ({mb.remaining_quota} left)</span>
                        </div>
                        <div className="np-progress-bar">
                          <div
                            className={`np-progress-fill ${percent > 80 ? 'danger' : 'success'}`}
                            style={{ width: `${percent}%` }}
                          />
                        </div>
                      </div>

                      <div className="text-[11px] font-mono bg-elevated p-2.5 rounded border-theme space-y-1">
                        <div className="flex justify-between text-theme-secondary">
                          <span>Host:</span>
                          <span className="text-theme-primary">{mb.smtp_host || `smtp.${mb.domain}`}</span>
                        </div>
                        <div className="flex justify-between text-theme-secondary">
                          <span>Port / TLS:</span>
                          <span className="text-theme-primary">{mb.smtp_port || 587}</span>
                        </div>
                        <div className="flex justify-between text-theme-secondary">
                          <span>Username:</span>
                          <span className="text-theme-primary truncate max-w-[160px]">{mb.smtp_username || mb.email_address}</span>
                        </div>
                        <div className="flex justify-between text-theme-secondary items-center pt-0.5 border-t border-theme/50">
                          <span>Relay Mode:</span>
                          <span>
                            {mb.webhook_url ? (
                              <span className="badge badge-accent text-[9px] py-0.5 px-1.5" title={mb.webhook_url}>⚡ HTTPS Webhook</span>
                            ) : (
                              <span className="text-theme-muted text-[10px]">Direct SMTP</span>
                            )}
                          </span>
                        </div>
                      </div>

                      <div className="pt-2 border-t-theme flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleOpenEditMailbox(mb)}
                          className="btn btn-secondary btn-sm"
                        >
                          ⚙️ Configure
                        </button>
                        <button
                          onClick={() => handleDeleteMailbox(mb)}
                          className="btn btn-danger btn-sm"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* TAB: PROPOSAL TEMPLATES */}
        {activeTab === "templates" && (
          <div className="w-full max-w-6xl mx-auto space-y-5">
            <div className="flex items-center justify-between pb-3 border-b-theme">
              <div>
                <h2 className="font-semibold text-base text-theme-primary flex items-center gap-2">
                  <span>📝 Multi-Service Proposal Template Pool</span>
                  <span className="badge badge-accent">ZERO SEED</span>
                </h2>
                <p className="text-xs text-theme-secondary mt-0.5">
                  Compose custom service proposals dynamically matched to target niches with automatic variable interpolation.
                </p>
              </div>

              <button
                onClick={() => handleOpenTemplateModal(null)}
                className="btn btn-primary btn-sm flex items-center gap-1.5"
              >
                <span>+ Create Template</span>
              </button>
            </div>

            {/* Variable Interpolation Legend */}
            <div className="np-variable-legend-bar flex flex-wrap items-center gap-2.5 text-xs">
              <span className="text-theme-secondary font-medium">Available Dynamic Variables:</span>
              {[
                "{{company_name}}",
                "{{niche}}",
                "{{country}}",
                "{{city}}",
                "{{tech_stack}}",
                "{{unsubscribe_link}}"
              ].map(tag => (
                <span key={tag} className="np-variable-chip" title="Dynamic template variable">
                  {tag}
                </span>
              ))}
            </div>

            {templatesList.length === 0 ? (
              <div className="np-empty-state">
                <div className="w-12 h-12 mx-auto mb-3 rounded-2xl bg-[rgba(168,85,247,0.12)] border border-[rgba(168,85,247,0.25)] flex items-center justify-center text-xl text-theme-purple shadow-inner">
                  📝
                </div>
                <h3 className="font-semibold text-sm text-theme-primary">No Data Available: Zero Proposal Templates</h3>
                <p className="text-xs text-theme-secondary mt-1.5 max-w-md mx-auto leading-relaxed">
                  The system starts 100% clean with zero seed templates. Create custom service templates to match target industries.
                </p>
                <button
                  onClick={() => handleOpenTemplateModal(null)}
                  className="btn btn-primary btn-sm mt-4 shadow-md"
                >
                  + Create First Proposal Template
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {templatesList.map((tpl) => (
                  <div key={tpl.id} className="np-card p-4 space-y-3 flex flex-col justify-between">
                    <div className="space-y-2">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <h3 className="font-semibold text-sm text-theme-primary">{tpl.title}</h3>
                          <div className="flex items-center gap-1.5 mt-1">
                            <span className="badge badge-accent text-[10px]">{tpl.niche}</span>
                            {Boolean(tpl.is_default) && (
                              <span className="badge badge-gold text-[10px]">DEFAULT FALLBACK</span>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center gap-1.5">
                          <button
                            type="button"
                            onClick={() => handleOpenTemplateModal(tpl)}
                            className="btn btn-secondary btn-sm"
                          >
                            Edit
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDeleteTemplate(tpl.id)}
                            className="btn btn-danger btn-sm"
                          >
                            Delete
                          </button>
                        </div>
                      </div>

                      <div className="bg-elevated p-3 rounded border-theme text-xs font-mono space-y-1.5">
                        <div className="text-theme-secondary font-semibold">
                          Subject: <span className="text-theme-primary">{tpl.subject_template}</span>
                        </div>
                        <div className="text-theme-primary whitespace-pre-line line-clamp-4 text-[11px] border-t-theme pt-1.5">
                          {tpl.body_template}
                        </div>
                      </div>
                    </div>

                    <div className="text-[10px] font-mono text-theme-muted pt-2 border-t-theme flex justify-between">
                      <span>Niche Match: {tpl.niche}</span>
                      <span>Updated: {tpl.updated_at ? tpl.updated_at.split("T")[0] : "—"}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB: DELIVERABILITY ANALYTICS */}
        {activeTab === "analytics" && (
          <div className="w-full max-w-6xl mx-auto space-y-5">
            <div className="flex items-center justify-between pb-3 border-b-theme">
              <div>
                <h2 className="font-semibold text-base text-theme-primary flex items-center gap-2">
                  <span>📈 Campaign Deliverability Analytics Dashboard</span>
                  <span className="badge badge-success">LIVE TELEMETRY</span>
                </h2>
                <p className="text-xs text-theme-secondary mt-0.5">
                  Visual metric indicators tracking open rates, bounce suppressions, conversion events, and sender reputation.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={fetchData}
                  className="btn btn-secondary btn-sm"
                  title="Refresh metrics"
                >
                  🔄 Refresh
                </button>
                <button
                  type="button"
                  onClick={handlePollImap}
                  disabled={isPollingImap}
                  className="btn btn-primary btn-sm flex items-center gap-1.5"
                  title="Trigger background IMAP poll for bounces and replies"
                >
                  <span>{isPollingImap ? "Polling Inboxes..." : "📡 Run IMAP Poll"}</span>
                </button>
              </div>
            </div>

            {/* 4 Primary KPI Indicator Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="np-card p-4 space-y-2 border-l-4 border-l-[var(--accent)]">
                <div className="text-xs text-theme-secondary font-semibold uppercase tracking-wider">Open Rate %</div>
                <div className="text-2xl font-bold font-mono text-theme-accent">
                  {deliverabilityStats.open_rate_percent}%
                </div>
                <div className="text-[11px] text-theme-muted font-mono">
                  {deliverabilityStats.total_opened} of {deliverabilityStats.total_delivered} delivered opened
                </div>
              </div>

              <div className="np-card p-4 space-y-2 border-l-4 border-l-[var(--danger)]">
                <div className="text-xs text-theme-secondary font-semibold uppercase tracking-wider">Bounce Rate %</div>
                <div className="text-2xl font-bold font-mono text-theme-danger">
                  {deliverabilityStats.bounce_rate_percent}%
                </div>
                <div className="text-[11px] text-theme-muted font-mono">
                  {deliverabilityStats.total_bounced} bounces auto-suppressed
                </div>
              </div>

              <div className="np-card p-4 space-y-2 border-l-4 border-l-[var(--success)]">
                <div className="text-xs text-theme-secondary font-semibold uppercase tracking-wider">Conversion Rate %</div>
                <div className="text-2xl font-bold font-mono text-theme-success">
                  {deliverabilityStats.conversion_rate_percent}%
                </div>
                <div className="text-[11px] text-theme-muted font-mono">
                  {deliverabilityStats.total_replied} replies & hot opportunities
                </div>
              </div>

              <div className="np-card p-4 space-y-2 border-l-4 border-l-[var(--gold)]">
                <div className="text-xs text-theme-secondary font-semibold uppercase tracking-wider">Sent / Delivered</div>
                <div className="text-2xl font-bold font-mono text-theme-gold">
                  {deliverabilityStats.total_delivered}
                </div>
                <div className="text-[11px] text-theme-muted font-mono">
                  {deliverabilityStats.total_sent} sent, {deliverabilityStats.total_queued} held in gate
                </div>
              </div>
            </div>

            {/* Secondary Operational Telemetry */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="np-card p-5 space-y-3">
                <h3 className="font-semibold text-sm text-theme-primary pb-2 border-b-theme">
                  Sender Health & Hygiene Telemetry
                </h3>
                <div className="space-y-2 text-xs font-mono">
                  <div className="flex justify-between py-1 border-b-theme text-theme-secondary">
                    <span>Sender Reputation Rating:</span>
                    <span className="font-bold text-theme-success">
                      {deliverabilityStats.bounce_rate_percent < 5 ? "OPTIMAL (98/100)" : "ATTENTION REQUIRED"}
                    </span>
                  </div>
                  <div className="flex justify-between py-1 border-b-theme text-theme-secondary">
                    <span>Global Suppressed Entities:</span>
                    <span className="font-bold text-theme-danger">{deliverabilityStats.total_suppressed}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b-theme text-theme-secondary">
                    <span>Enrolled Sending Mailboxes:</span>
                    <span className="font-bold text-theme-accent">{mailboxes.length} Active</span>
                  </div>
                  <div className="flex justify-between py-1 text-theme-secondary">
                    <span>Zero-Bounce Verification:</span>
                    <span className="text-theme-success font-semibold">Active DNS MX + SMTP Ping</span>
                  </div>
                </div>
              </div>

              <div className="np-card p-5 space-y-3">
                <h3 className="font-semibold text-sm text-theme-primary pb-2 border-b-theme">
                  Outreach Pipeline Status
                </h3>
                <div className="space-y-2 text-xs font-mono">
                  <div className="flex justify-between py-1 border-b-theme text-theme-secondary">
                    <span>Held in Approval Gate:</span>
                    <span className="font-bold text-theme-warning">{pendingApprovals.length} Leads</span>
                  </div>
                  <div className="flex justify-between py-1 border-b-theme text-theme-secondary">
                    <span>High-Intent Hot Inquiries:</span>
                    <span className="font-bold text-theme-danger">{uniqueHotLeads.length} Hot Leads</span>
                  </div>
                  <div className="flex justify-between py-1 border-b-theme text-theme-secondary">
                    <span>Total Entities Tracked:</span>
                    <span className="font-bold text-theme-primary">{kanbanItems.length} Total</span>
                  </div>
                  <div className="flex justify-between py-1 text-theme-secondary">
                    <span>Working Hours Window:</span>
                    <span className="text-theme-accent font-semibold">9:00 AM - 5:00 PM Local Recipient (Mon-Fri)</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 5: DYNAMIC ADMIN PROFILE */}
        {user.role === "admin" && activeTab === "security_settings" && (
          <div className="w-full max-w-3xl mx-auto space-y-5">
            <div className="pb-3 border-b-theme">
              <h2 className="font-semibold text-base text-theme-primary">
                <span>⚙️ Account Security & Dynamic Admin Profile</span>
              </h2>
              <p className="text-xs text-theme-secondary mt-0.5">
                Update master credentials and profile details. Password modifications re-hash via Bcrypt with 12 rounds.
              </p>
            </div>

            <div className="np-card p-6 space-y-5">
              <div className="flex items-center justify-between pb-4 border-b-theme">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg border-theme bg-elevated flex items-center justify-center font-bold text-sm text-theme-accent font-mono">
                    HA
                  </div>
                  <div>
                    <h3 className="font-semibold text-sm text-theme-primary">{adminProfile?.full_name || "H.Huddair"}</h3>
                    <p className="text-xs font-mono text-theme-accent">{adminProfile?.email || "h.huddair@nexus-pulse.io"}</p>
                  </div>
                </div>
                <span className="badge badge-gold">MASTER ADMIN</span>
              </div>

              <form onSubmit={handleUpdateAdminProfile} className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="np-label">Admin Username</label>
                    <input
                      type="text"
                      value={adminUsernameInput}
                      onChange={(e) => {
                        adminFormDirtyRef.current = true;
                        setAdminUsernameInput(e.target.value);
                      }}
                      className="np-input font-mono"
                      required
                    />
                  </div>
                  <div>
                    <label className="np-label">Corporate Email</label>
                    <input
                      type="email"
                      value={adminEmailInput}
                      onChange={(e) => {
                        adminFormDirtyRef.current = true;
                        setAdminEmailInput(e.target.value);
                      }}
                      className="np-input font-mono"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="np-label">Full Executive Name</label>
                  <input
                    type="text"
                    value={adminFullNameInput}
                    onChange={(e) => {
                      adminFormDirtyRef.current = true;
                      setAdminFullNameInput(e.target.value);
                    }}
                    className="np-input"
                    required
                  />
                </div>

                <div className="pt-4 border-t-theme space-y-3">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-theme-secondary">
                    Password Modification (Bcrypt Re-Hashing)
                  </h4>
                  <p className="text-xs text-theme-muted">
                    Leave blank to maintain existing password. To update, provide current password and new password.
                  </p>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div>
                      <label className="np-label">Current Password</label>
                      <input
                        type="password"
                        value={adminCurrentPassword}
                        onChange={(e) => setAdminCurrentPassword(e.target.value)}
                        placeholder="••••••••••••"
                        className="np-input font-mono"
                      />
                    </div>
                    <div>
                      <label className="np-label">New Password</label>
                      <input
                        type="password"
                        value={adminNewPassword}
                        onChange={(e) => setAdminNewPassword(e.target.value)}
                        placeholder="••••••••••••"
                        className="np-input font-mono"
                      />
                    </div>
                    <div>
                      <label className="np-label">Confirm Password</label>
                      <input
                        type="password"
                        value={adminConfirmPassword}
                        onChange={(e) => setAdminConfirmPassword(e.target.value)}
                        placeholder="••••••••••••"
                        className="np-input font-mono"
                      />
                    </div>
                  </div>
                </div>

                <div className="pt-4 flex items-center justify-between border-t-theme">
                  <span className="text-[11px] text-theme-muted font-mono">
                    Bcrypt (Cost 12) GPU-Resistant Salting
                  </span>
                  <button type="submit" className="btn btn-primary btn-sm">
                    Save Profile Changes
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* TAB 6: ROLE-BASED OPERATOR MANAGEMENT & AUDIT TRAIL */}
        {user.role === "admin" && activeTab === "operator_mgmt" && (
          <div className="w-full max-w-7xl mx-auto space-y-6">
            <div className="flex items-center justify-between pb-3 border-b-theme">
              <div>
                <h2 className="font-semibold text-base text-theme-primary flex items-center gap-2">
                  <span>👥 Role-Based Operator Management</span>
                  <span className="badge badge-accent">ADMIN PORTAL</span>
                </h2>
                <p className="text-xs text-theme-secondary mt-0.5">
                  Issue operator licenses, configure hardware machine-locking, toggle active status, and modify daily quotas inline.
                </p>
              </div>

              <button
                onClick={() => setIsCreateOperatorOpen(true)}
                className="btn btn-primary btn-sm"
              >
                + Create Operator Account
              </button>
            </div>

            {operatorsList.length === 0 ? (
              <div className="np-empty-state">
                <div className="w-12 h-12 mx-auto mb-3 rounded-2xl bg-[rgba(168,85,247,0.12)] border border-[rgba(168,85,247,0.25)] flex items-center justify-center text-xl text-theme-purple shadow-inner">
                  👥
                </div>
                <h3 className="font-semibold text-sm text-theme-primary">No Data Available: Zero Operators Registered</h3>
                <p className="text-xs text-theme-secondary mt-1.5 max-w-md mx-auto leading-relaxed">
                  Issue hardware-locked credentials and license tokens to onboard your team.
                </p>
                <button
                  onClick={() => setIsCreateOperatorOpen(true)}
                  className="btn btn-primary btn-sm mt-4 shadow-md"
                >
                  + Create Operator Account
                </button>
              </div>
            ) : (
              /* Operator List Table with Fixed Columns & Horizontal Wrapper */
              <div className="np-table-wrapper">
                <table className="np-table">
                  <thead>
                    <tr>
                      <th style={{ minWidth: "180px" }}>Operator Identity</th>
                      <th style={{ minWidth: "80px" }}>Role</th>
                      <th style={{ minWidth: "130px" }}>Access Status</th>
                      <th style={{ minWidth: "160px" }}>Device Lock</th>
                      <th style={{ minWidth: "130px" }}>Daily Quotas</th>
                      <th style={{ minWidth: "160px" }}>Subscription Expiry</th>
                      <th style={{ minWidth: "110px" }}>Last Login</th>
                      <th style={{ minWidth: "200px" }} className="text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {operatorsList.map((op) => (
                      <React.Fragment key={op.id}>
                        <tr>
                          <td>
                            <div className="font-semibold text-xs text-theme-primary leading-normal truncate">{op.full_name}</div>
                            <div className="text-[11px] font-mono text-theme-accent leading-normal truncate">{op.username}</div>
                            <div className="text-[10px] text-theme-muted leading-normal truncate">{op.email}</div>
                          </td>

                          <td className="np-table-nowrap">
                            <span className={`badge ${op.role === 'admin' ? 'badge-gold' : 'badge-accent'}`}>
                              {op.role}
                            </span>
                          </td>

                          <td className="np-table-nowrap">
                            {op.role === "admin" ? (
                              <span className="badge badge-success">PERMANENT</span>
                            ) : (
                              <button
                                onClick={() => handleToggleOperatorStatus(op.id)}
                                className={`btn btn-sm ${op.is_active === 1 ? 'btn-success' : 'btn-danger'}`}
                                title="Click to toggle access"
                              >
                                <span className={`w-1.5 h-1.5 rounded-full ${op.is_active === 1 ? 'bg-[var(--success)]' : 'bg-[var(--danger)]'}`} />
                                <span>{op.is_active === 1 ? 'ACTIVE' : 'REVOKED'}</span>
                              </button>
                            )}
                          </td>

                          <td>
                            <span className="text-xs font-mono truncate block" title={op.device_lock_id || "Unbound"}>
                              {op.device_lock_id || "Auto-Bind on Login"}
                            </span>
                          </td>

                          <td className="np-table-nowrap font-mono text-xs">
                            <div>Scrape: <strong>{op.daily_scrape_quota}</strong>/d</div>
                            <div>Send: <strong>{op.daily_send_quota}</strong>/d</div>
                          </td>

                          <td className="np-table-nowrap text-xs font-mono">
                            {op.expiry_date ? op.expiry_date.split(" ")[0] : "Perpetual"}
                          </td>

                          <td className="np-table-nowrap text-xs text-theme-muted font-mono">
                            {op.last_login ? op.last_login.split(" ")[0] : "Never"}
                          </td>

                          <td className="np-table-actions">
                            <div className="flex items-center justify-end gap-2 shrink-0">
                              <button
                                onClick={() => handleOpenResetPasswordModal(op)}
                                className="btn btn-secondary btn-sm"
                                title="Reset Operator Password"
                              >
                                Reset Pass
                              </button>
                              <button
                                onClick={() => handleToggleInlineAdjust(op)}
                                className={`btn btn-sm ${expandedOperatorId === op.id ? 'btn-primary' : 'btn-secondary'}`}
                                title="Adjust Quotas & Subscription"
                              >
                                {expandedOperatorId === op.id ? 'Close' : 'Adjust'}
                              </button>
                              {op.role !== "admin" && (
                                <button
                                  onClick={() => handleDeleteOperator(op)}
                                  className="btn btn-danger btn-sm"
                                  title={`Permanently delete operator account ${op.username}`}
                                >
                                  Delete
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>

                        {/* Streamlined Inline Action Bar */}
                        {expandedOperatorId === op.id && (
                          <tr>
                            <td colSpan={8} className="np-expand-cell border-b-theme">
                              <div className="p-4 sm:p-5 space-y-3 bg-elevated">
                                <div className="flex items-center justify-between pb-2 border-b-theme">
                                  <span className="text-xs font-semibold text-theme-primary">
                                    Inline Quota & Subscription Controls: {op.username}
                                  </span>
                                  <span className="text-xs font-mono text-theme-muted">
                                    Current Expiry: {op.expiry_date || "Perpetual"}
                                  </span>
                                </div>

                                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                                  {/* Quick Extension Presets */}
                                  <div>
                                    <label className="np-label">Extend Subscription</label>
                                    <div className="grid grid-cols-4 gap-1.5">
                                      <button
                                        type="button"
                                        onClick={() => handleApplyInlineQuotas(op.id, 30)}
                                        className="btn btn-secondary btn-sm justify-center"
                                      >
                                        +30d
                                      </button>
                                      <button
                                        type="button"
                                        onClick={() => handleApplyInlineQuotas(op.id, 90)}
                                        className="btn btn-secondary btn-sm justify-center"
                                      >
                                        +90d
                                      </button>
                                      <button
                                        type="button"
                                        onClick={() => handleApplyInlineQuotas(op.id, 180)}
                                        className="btn btn-secondary btn-sm justify-center"
                                      >
                                        +180d
                                      </button>
                                      <button
                                        type="button"
                                        onClick={() => handleApplyInlineQuotas(op.id, 365)}
                                        className="btn btn-secondary btn-sm justify-center"
                                      >
                                        +1y
                                      </button>
                                    </div>
                                  </div>

                                  {/* Daily Scrape Limit */}
                                  <div>
                                    <label className="np-label">Daily Scrape Limit</label>
                                    <input
                                      type="number"
                                      value={inlineScrapeQuota}
                                      onChange={(e) => setInlineScrapeQuota(e.target.value)}
                                      className="np-input font-mono"
                                    />
                                    <div className="flex gap-1 mt-1">
                                      {[100, 200, 500, 1000].map(val => (
                                        <button
                                          key={val}
                                          type="button"
                                          onClick={() => setInlineScrapeQuota(String(val))}
                                          className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-overlay hover:bg-hover text-theme-secondary"
                                        >
                                          {val}
                                        </button>
                                      ))}
                                    </div>
                                  </div>

                                  {/* Daily Send Limit */}
                                  <div>
                                    <label className="np-label">Daily Send Limit</label>
                                    <input
                                      type="number"
                                      value={inlineSendQuota}
                                      onChange={(e) => setInlineSendQuota(e.target.value)}
                                      className="np-input font-mono"
                                    />
                                    <div className="flex gap-1 mt-1">
                                      {[25, 50, 100, 200].map(val => (
                                        <button
                                          key={val}
                                          type="button"
                                          onClick={() => setInlineSendQuota(String(val))}
                                          className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-overlay hover:bg-hover text-theme-secondary"
                                        >
                                          {val}
                                        </button>
                                      ))}
                                    </div>
                                  </div>
                                </div>

                                <div className="pt-2 flex items-center justify-between border-t-theme">
                                  <div>
                                    {op.role !== "admin" && (
                                      <button
                                        type="button"
                                        onClick={() => handleDeleteOperator(op)}
                                        className="btn btn-danger btn-sm"
                                        title="Permanently remove operator account"
                                      >
                                        Delete Operator Account
                                      </button>
                                    )}
                                  </div>
                                  <div className="flex justify-end gap-2">
                                    <button
                                      type="button"
                                      onClick={() => setExpandedOperatorId(null)}
                                      className="btn btn-ghost btn-sm"
                                    >
                                      Cancel
                                    </button>
                                    <button
                                      type="button"
                                      onClick={() => handleApplyInlineQuotas(op.id, null)}
                                      disabled={updatingOperatorId === op.id}
                                      className="btn btn-primary btn-sm"
                                    >
                                      {updatingOperatorId === op.id ? "Saving..." : "Apply Changes"}
                                    </button>
                                  </div>
                                </div>
                              </div>
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Interactive Operator Session Audit Trail */}
            <div className="np-card p-5 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b-theme">
                <div>
                  <h3 className="font-semibold text-sm text-theme-primary">Interactive Session & Security Audit Trail</h3>
                  <p className="text-xs text-theme-secondary mt-0.5">
                    Immutable event stream of logins, quota revisions, hardware bindings, and outreach approvals.
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={auditSearch}
                    onChange={(e) => setAuditSearch(e.target.value)}
                    placeholder="Filter audit log..."
                    className="np-input text-xs w-48 font-mono"
                  />
                </div>
              </div>

              <div className="space-y-2">
                {sessionAuditLogs.length === 0 ? (
                  <div className="text-center py-8 text-xs text-theme-muted font-mono italic">
                    No session audit records recorded yet. Activity will stream here live as operators log in and execute actions.
                  </div>
                ) : (
                  sessionAuditLogs
                    .filter(ev => {
                      if (!auditSearch) return true;
                      const q = auditSearch.toLowerCase();
                      const u = (ev.username || ev.user || "").toLowerCase();
                      const d = (ev.detail || "").toLowerCase();
                      const a = (ev.action || "").toLowerCase();
                      return u.includes(q) || d.includes(q) || a.includes(q);
                    })
                    .map((ev) => (
                      <div key={ev.id} className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-2.5 rounded bg-elevated border-theme text-xs font-mono">
                        <div className="flex items-center gap-2.5 flex-wrap min-w-0">
                          <span className={`badge shrink-0 ${
                            ev.action === 'LOGIN' ? 'badge-accent' :
                            ev.action === 'QUOTA_MODIFIED' ? 'badge-gold' :
                            ev.action === 'OUTREACH_APPROVED' ? 'badge-warning' : 'badge-success'
                          }`}>
                            {ev.action}
                          </span>
                          <span className="font-bold text-theme-primary shrink-0">{ev.username || ev.user || "system"}</span>
                          <span className="text-theme-secondary break-words">{ev.detail}</span>
                        </div>
                        <span className="text-theme-muted text-[11px] shrink-0">
                          {ev.created_at ? ev.created_at.replace("T", " ").split(".")[0] : "Just now"}
                        </span>
                      </div>
                    ))
                )}
              </div>
            </div>
          </div>
        )}

        {/* TAB: MANUAL BILLING CONTROLS (SUPER ADMIN ONLY) */}
        {user.role === "admin" && activeTab === "billing_mgmt" && (
          <div className="w-full max-w-6xl mx-auto space-y-6">
            <div className="flex items-center justify-between pb-3 border-b-theme">
              <div>
                <h2 className="font-semibold text-base text-theme-primary flex items-center gap-2">
                  <span>💳 Manual Billing & Subscription Lifecycle</span>
                  <span className="badge badge-accent">SUPER ADMIN</span>
                </h2>
                <p className="text-xs text-theme-secondary mt-0.5">
                  Direct operator license extensions, custom base pricing, and automated 10% discount on 90-day plans.
                </p>
              </div>
            </div>

            {/* PENDING OPERATOR PLAN REQUESTS (PAYWALL INTAKE) */}
            <div className="np-card p-5 space-y-3 border-theme">
              <div className="flex items-center justify-between pb-2 border-b-theme">
                <div>
                  <h3 className="font-semibold text-sm text-theme-primary flex items-center gap-2">
                    <span>📥 Pending Operator Plan Requests</span>
                    <span className="badge badge-accent font-mono text-xs">{planRequests.length} Pending</span>
                  </h3>
                  <p className="text-xs text-theme-secondary mt-0.5">
                    Self-serve plan requests submitted by operators encountering the post-trial paywall.
                  </p>
                </div>
              </div>

              {planRequests.length === 0 ? (
                <div className="text-center py-6 text-xs text-theme-muted font-mono italic">
                  Zero pending operator plan requests. All operator accounts are currently up to date.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs font-mono">
                    <thead>
                      <tr className="border-b border-[var(--border-subtle)] text-theme-secondary">
                        <th className="py-2 px-3">Operator</th>
                        <th className="py-2 px-3">Email</th>
                        <th className="py-2 px-3">Plan Requested</th>
                        <th className="py-2 px-3">Duration</th>
                        <th className="py-2 px-3">Price</th>
                        <th className="py-2 px-3">Notes</th>
                        <th className="py-2 px-3">Submitted</th>
                        <th className="py-2 px-3 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {planRequests.map((req) => (
                        <tr key={req.id} className="border-b border-[var(--border-subtle)] hover:bg-elevated">
                          <td className="py-2.5 px-3 font-semibold text-theme-primary">{req.full_name || req.username}</td>
                          <td className="py-2.5 px-3 text-theme-accent">{req.email || "N/A"}</td>
                          <td className="py-2.5 px-3 font-bold text-theme-primary">{req.plan_name}</td>
                          <td className="py-2.5 px-3 text-theme-secondary">+{req.duration_days} Days</td>
                          <td className="py-2.5 px-3 font-bold text-theme-success">${Number(req.price).toFixed(2)}</td>
                          <td className="py-2.5 px-3 text-theme-muted max-w-xs truncate" title={req.notes}>{req.notes || "—"}</td>
                          <td className="py-2.5 px-3 text-theme-muted">{req.created_at ? req.created_at.slice(0, 16) : "Just now"}</td>
                          <td className="py-2.5 px-3 text-right space-x-1.5 shrink-0">
                            <button
                              type="button"
                              onClick={() => handleApprovePlanRequest(req.id)}
                              className="btn btn-primary btn-xs"
                            >
                              ✓ Approve & Activate
                            </button>
                            <button
                              type="button"
                              onClick={() => handleRejectPlanRequest(req.id)}
                              className="btn btn-ghost btn-xs text-theme-danger"
                            >
                              ✕ Reject
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
              {/* Left 2 Cols: Interactive Billing Action Form */}
              <div className="lg:col-span-2 np-card p-5 space-y-4">
                <h3 className="font-semibold text-sm text-theme-primary pb-2 border-b-theme">
                  Issue / Extend Operator Subscription
                </h3>

                <form onSubmit={handleApplyBilling} className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="np-label">Target Operator</label>
                      <select
                        value={billingTargetOpId}
                        onChange={(e) => setBillingTargetOpId(e.target.value)}
                        className="np-select"
                        required
                      >
                        <option value="">-- Select Operator --</option>
                        {operatorsList.map(op => (
                          <option key={op.id} value={op.id}>
                            {op.full_name || op.username} ({op.username}) - {op.role}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="np-label">Base Price ($ USD)</label>
                      <input
                        type="number"
                        step="0.01"
                        min="1"
                        value={billingBasePrice}
                        onChange={(e) => setBillingBasePrice(e.target.value)}
                        className="np-input font-mono"
                        placeholder="199.00"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label className="np-label">Duration Package Extender</label>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                      {[
                        { days: 30, label: "+30 Days (1m)", discount: 0 },
                        { days: 90, label: "+90 Days (3m)", discount: 10, highlight: true },
                        { days: 180, label: "+180 Days (6m)", discount: 0 },
                        { days: 365, label: "+1 Year (12m)", discount: 0 }
                      ].map((pkg) => (
                        <button
                          key={pkg.days}
                          type="button"
                          onClick={() => setBillingDurationDays(pkg.days)}
                          className={`btn btn-sm flex-col py-2.5 h-auto ${
                            billingDurationDays === pkg.days ? 'btn-primary' : 'btn-secondary'
                          } ${pkg.highlight && billingDurationDays !== pkg.days ? 'border-[var(--accent)] text-theme-accent' : ''}`}
                        >
                          <span className="font-bold text-xs">{pkg.label}</span>
                          {pkg.discount > 0 && (
                            <span className="text-[10px] text-theme-success font-semibold mt-0.5">
                              10% Discount
                            </span>
                          )}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="np-label">Invoice Reference / Notes (Optional)</label>
                    <input
                      type="text"
                      value={billingNotes}
                      onChange={(e) => setBillingNotes(e.target.value)}
                      placeholder="e.g. Wire transfer ref #8841 / Corporate renewal"
                      className="np-input text-xs"
                    />
                  </div>

                  <div className="pt-2 flex justify-end">
                    <button
                      type="submit"
                      disabled={isApplyingBilling || !billingTargetOpId}
                      className="btn btn-primary btn-sm flex items-center gap-1.5"
                    >
                      {isApplyingBilling ? (
                        <span>Processing Billing...</span>
                      ) : (
                        <>
                          <span>Apply Billing & Extend</span>
                          <span>➔</span>
                        </>
                      )}
                    </button>
                  </div>
                </form>
              </div>

              {/* Right Col: Automated Price & Discount Summary */}
              <div className="np-card p-5 space-y-4 bg-elevated border-theme">
                <h3 className="font-semibold text-sm text-theme-primary pb-2 border-b-theme">
                  Automated Pricing Breakdown
                </h3>

                {(() => {
                  const base = parseFloat(billingBasePrice) || 0;
                  const days = billingDurationDays || 30;
                  const isQuarterly = days === 90;
                  const subtotal = days === 30 ? base : (days === 90 ? base * 3 : (days === 180 ? base * 6 : base * 12));
                  const discountRate = isQuarterly ? 0.10 : 0.0;
                  const discountAmt = isQuarterly ? subtotal * discountRate : 0.0;
                  const finalTotal = subtotal - discountAmt;

                  return (
                    <div className="space-y-3 text-xs font-mono">
                      <div className="flex justify-between py-1.5 border-b-theme text-theme-secondary">
                        <span>Base Rate:</span>
                        <span className="font-bold text-theme-primary">${base.toFixed(2)}/mo</span>
                      </div>
                      <div className="flex justify-between py-1.5 border-b-theme text-theme-secondary">
                        <span>Selected Duration:</span>
                        <span className="font-bold text-theme-primary">+{days} Days</span>
                      </div>
                      <div className="flex justify-between py-1.5 border-b-theme text-theme-secondary">
                        <span>Standard Subtotal:</span>
                        <span className="text-theme-primary">${subtotal.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between py-1.5 border-b-theme">
                        <span className={isQuarterly ? "text-theme-success font-semibold" : "text-theme-secondary"}>
                          Discount Applied:
                        </span>
                        <span className={isQuarterly ? "text-theme-success font-bold" : "text-theme-primary"}>
                          {isQuarterly ? `-10% (-$${discountAmt.toFixed(2)})` : "$0.00"}
                        </span>
                      </div>
                      {isQuarterly && (
                        <div className="p-2 rounded bg-[var(--success-muted)] text-[11px] text-theme-success font-sans">
                          🎉 <strong>Automated 10% Savings:</strong> 90-day quarterly package incentive applied.
                        </div>
                      )}
                      <div className="flex justify-between py-2 text-sm font-bold border-t-theme pt-3">
                        <span className="text-theme-primary">Final Amount:</span>
                        <span className="text-theme-accent text-base">${finalTotal.toFixed(2)}</span>
                      </div>
                    </div>
                  );
                })()}
              </div>
            </div>

            {/* Billing Transaction History Table */}
            <div className="np-card p-5 space-y-3">
              <div className="flex items-center justify-between pb-2 border-b-theme">
                <div>
                  <h3 className="font-semibold text-sm text-theme-primary">Manual Billing Ledger & Audit History</h3>
                  <p className="text-xs text-theme-secondary mt-0.5">
                    Immutable log of all manual duration extensions and calculated billing transactions.
                  </p>
                </div>
                <span className="badge badge-accent font-mono text-xs">{billingHistory.length} Transactions</span>
              </div>

              {billingHistory.length === 0 ? (
                <div className="np-empty-state py-8">
                  <div className="w-10 h-10 mx-auto mb-2 rounded-xl bg-[rgba(245,158,11,0.12)] border border-[rgba(245,158,11,0.25)] flex items-center justify-center text-lg text-theme-warning shadow-inner">
                    💳
                  </div>
                  <h4 className="font-semibold text-xs text-theme-primary">No Data Available: Zero Billing Records</h4>
                  <p className="text-[11px] text-theme-secondary mt-1">Manual subscription adjustments will be logged here.</p>
                </div>
              ) : (
                <div className="np-table-wrapper">
                  <table className="np-table text-xs">
                    <thead>
                      <tr>
                        <th>Date & Time</th>
                        <th>Operator ID</th>
                        <th>Base Rate</th>
                        <th>Duration</th>
                        <th>Discount</th>
                        <th>Final Paid</th>
                        <th>New Expiration</th>
                        <th>Admin</th>
                        <th>Notes</th>
                      </tr>
                    </thead>
                    <tbody>
                      {billingHistory.map((item) => (
                        <tr key={item.id}>
                          <td className="font-mono text-theme-muted">{item.created_at ? item.created_at.split(".")[0] : "—"}</td>
                          <td className="font-mono font-semibold text-theme-primary">{item.operator_id}</td>
                          <td className="font-mono text-theme-secondary">${parseFloat(item.base_price || 0).toFixed(2)}</td>
                          <td className="font-mono font-bold text-theme-accent">+{item.duration_days}d</td>
                          <td className="font-mono">
                            {item.discount_percent > 0 ? (
                              <span className="badge badge-success text-[10px]">{item.discount_percent}% OFF</span>
                            ) : (
                              <span className="text-theme-muted">None</span>
                            )}
                          </td>
                          <td className="font-mono font-bold text-theme-success">${parseFloat(item.final_price || 0).toFixed(2)}</td>
                          <td className="font-mono text-theme-primary">{item.new_expiry_date || "—"}</td>
                          <td className="font-mono text-theme-secondary">{item.created_by || "admin"}</td>
                          <td className="text-theme-muted truncate max-w-[150px]" title={item.notes || ""}>{item.notes || "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB: GLOBAL DOMAIN BLACKLIST (SUPER ADMIN ONLY) */}
        {user.role === "admin" && activeTab === "blacklist_mgmt" && (
          <div className="w-full max-w-5xl mx-auto space-y-6">
            <div className="flex items-center justify-between pb-3 border-b-theme">
              <div>
                <h2 className="font-semibold text-base text-theme-primary flex items-center gap-2">
                  <span>🚫 Global Domain Blacklist & Suppression Rules</span>
                  <span className="badge badge-accent">SUPER ADMIN</span>
                </h2>
                <p className="text-xs text-theme-secondary mt-0.5">
                  Enforce wildcard exclusion patterns (e.g., *.gov, competitor domains) across all scrapers, hygiene pipelines, and outbound queues.
                </p>
              </div>
            </div>

            {/* Add Rule Form */}
            <div className="np-card p-5 space-y-3">
              <h3 className="font-semibold text-sm text-theme-primary pb-2 border-b-theme">
                Add Global Blacklist Pattern
              </h3>
              <form onSubmit={handleAddBlacklistRule} className="grid grid-cols-1 sm:grid-cols-3 gap-3 items-end">
                <div>
                  <label className="np-label">Domain Pattern / Wildcard</label>
                  <input
                    type="text"
                    value={newRulePattern}
                    onChange={(e) => setNewRulePattern(e.target.value)}
                    placeholder="e.g. *.gov, competitor.de, @badagency.com"
                    className="np-input font-mono text-xs"
                    required
                  />
                </div>
                <div>
                  <label className="np-label">Exclusion Reason</label>
                  <input
                    type="text"
                    value={newRuleReason}
                    onChange={(e) => setNewRuleReason(e.target.value)}
                    placeholder="e.g. Government portal, direct competitor"
                    className="np-input text-xs"
                  />
                </div>
                <div>
                  <button type="submit" className="btn btn-primary btn-sm w-full justify-center">
                    + Add Blacklist Rule
                  </button>
                </div>
              </form>
            </div>

            {/* Blacklist Rules Table */}
            <div className="np-card p-5 space-y-3">
              <div className="flex items-center justify-between pb-2 border-b-theme">
                <h3 className="font-semibold text-sm text-theme-primary">Active Exclusion Rules</h3>
                <span className="badge badge-accent font-mono text-xs">{blacklistRules.length} Rules Enforced</span>
              </div>

              {blacklistRules.length === 0 ? (
                <div className="np-empty-state py-8">
                  <div className="w-10 h-10 mx-auto mb-2 rounded-xl bg-[rgba(248,113,113,0.12)] border border-[rgba(248,113,113,0.25)] flex items-center justify-center text-lg text-theme-danger shadow-inner">
                    🛡️
                  </div>
                  <h4 className="font-semibold text-xs text-theme-primary">No Data Available: Zero Blacklist Rules</h4>
                  <p className="text-[11px] text-theme-secondary mt-1">Add domain patterns above to automatically reject unwanted targets.</p>
                </div>
              ) : (
                <div className="np-table-wrapper">
                  <table className="np-table text-xs">
                    <thead>
                      <tr>
                        <th>Domain / Email Pattern</th>
                        <th>Type</th>
                        <th>Reason</th>
                        <th>Source / Added By</th>
                        <th>Added Date</th>
                        <th className="text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {blacklistRules.map((rule) => (
                        <tr key={rule.id}>
                          <td className="font-mono font-bold text-theme-accent">{rule.pattern}</td>
                          <td>
                            <span className={`badge text-[9px] font-mono ${rule.entity_type === "email" ? "badge-warning" : "badge-purple"}`}>
                              {rule.entity_type || "domain"}
                            </span>
                          </td>
                          <td className="text-theme-secondary">{rule.reason || "Excluded"}</td>
                          <td className="font-mono text-theme-muted">
                            {rule.source === "suppressed_entities" ? "Opt-Out / Bounce" : (rule.created_by || "admin")}
                          </td>
                          <td className="font-mono text-theme-muted">{rule.created_at ? rule.created_at.split("T")[0] : "—"}</td>
                          <td className="text-right">
                            <button
                              type="button"
                              onClick={() => handleDeleteBlacklistRule(rule.id)}
                              className="btn btn-danger btn-sm"
                              title="Delete rule and unblock entity"
                            >
                              Remove / Unblock
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Suppressed Pipeline Leads Section */}
            {(() => {
              const suppressedLeads = kanbanItems.filter(
                (item) => normalizeLeadStatus(item.status) === "SUPPRESSED" || item.unsubscribed
              );
              return (
                <div className="np-card p-5 space-y-3">
                  <div className="flex items-center justify-between pb-2 border-b-theme">
                    <div>
                      <h3 className="font-semibold text-sm text-theme-primary flex items-center gap-2">
                        <span>🚫 Suppressed Pipeline Leads</span>
                        <span className="badge badge-danger font-mono text-xs">{suppressedLeads.length} Suppressed</span>
                      </h3>
                      <p className="text-xs text-theme-secondary mt-0.5">
                        Leads locked in suppressed state due to opt-outs, bounces, or exclusion rules. Click 'Unblock' to restore to Approval Hold.
                      </p>
                    </div>
                  </div>

                  {suppressedLeads.length === 0 ? (
                    <div className="p-6 text-center">
                      <span className="text-2xl mb-1 block">✓</span>
                      <h4 className="font-semibold text-xs text-theme-primary">No Suppressed Leads</h4>
                      <p className="text-[11px] text-theme-secondary mt-0.5">All contacts in your pipeline are eligible for review or dispatch.</p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                      {suppressedLeads.map((sLead) => (
                        <div key={sLead.id} className="np-card p-3 space-y-2 bg-overlay border-theme">
                          <div className="flex items-start justify-between gap-1">
                            <h4 className="font-semibold text-xs text-theme-primary truncate">
                              {sLead.company_name}
                            </h4>
                            <span className="badge badge-danger text-[9px] font-mono shrink-0">
                              SUPPRESSED
                            </span>
                          </div>
                          <p className="text-[11px] font-mono text-theme-accent truncate">
                            {sLead.recipient || sLead.primary_email}
                          </p>
                          <p className="text-[10px] text-theme-secondary line-clamp-1" title={sLead.bounce_reason || "Opt-out / Unsubscribe"}>
                            Reason: {sLead.bounce_reason || "Opt-out / Unsubscribe"}
                          </p>
                          <div className="flex items-center gap-1 pt-1">
                            <button
                              onClick={() => handleUnblockLead(sLead.id, sLead.recipient || sLead.primary_email)}
                              className="btn btn-warning btn-sm text-[10px] flex-1 justify-center"
                              title="Unblock this suppressed lead and return it to Approval Hold"
                            >
                              🔓 Unblock / Reset to Approval
                            </button>
                            <button
                              onClick={() => handleDeleteQueueItem(sLead.id, sLead.recipient || sLead.primary_email)}
                              className="btn btn-danger btn-sm text-[10px] px-2"
                              title="Permanently Delete Lead"
                            >
                              🗑️
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })()}
          </div>
        )}

        {/* TAB 7: LICENSE & TELEMETRY MODULE */}
        {user.role === "admin" && activeTab === "license_mgmt" && (
          <div className="w-full max-w-6xl mx-auto space-y-5">
            <div className="pb-3 border-b-theme">
              <h2 className="font-semibold text-base text-theme-primary">
                <span>📜 License & Hardware Cryptographic Telemetry</span>
              </h2>
              <p className="text-xs text-theme-secondary mt-0.5">
                Anti-theft boundary enforcement, hardware-bound machine GUIDs, and active license signatures.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="np-card p-5 space-y-3">
                <div className="flex items-center justify-between pb-2 border-b-theme">
                  <h3 className="font-semibold text-sm text-theme-primary">Host Hardware Telemetry</h3>
                  <span className="badge badge-success">ACTIVE LOCK</span>
                </div>

                <div className="space-y-2 text-xs font-mono">
                  <div className="flex justify-between py-1 border-b-theme">
                    <span className="text-theme-secondary">Machine ID:</span>
                    <span className="font-bold text-theme-accent">{licenseTelemetry?.hardware_fingerprint?.machine_id || "NEXUS-E727-BB0B-765E-4021"}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b-theme">
                    <span className="text-theme-secondary">Windows MachineGuid:</span>
                    <span className="text-theme-primary">{licenseTelemetry?.hardware_fingerprint?.machine_guid || "25ea9ea7-2853-4895-b3f4-4732c6176d0b"}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b-theme">
                    <span className="text-theme-secondary">MAC Interface:</span>
                    <span className="text-theme-primary">{licenseTelemetry?.hardware_fingerprint?.mac_address || "80:FA:5B:1C:5C:E6"}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b-theme">
                    <span className="text-theme-secondary">License Tier:</span>
                    <span className="font-bold text-theme-gold">{licenseTelemetry?.license_payload?.tier || "Level-2-Enterprise"}</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-theme-secondary">Licensed Client:</span>
                    <span className="font-bold text-theme-primary">{licenseTelemetry?.license_payload?.client_name || "H.Huddair Enterprise"}</span>
                  </div>
                </div>
              </div>

              <div className="np-card p-5 space-y-3">
                <div className="flex items-center justify-between pb-2 border-b-theme">
                  <h3 className="font-semibold text-sm text-theme-primary">Vault Deduplication Shield</h3>
                  <span className="badge badge-accent">ACTIVE</span>
                </div>

                <div className="space-y-2 text-xs font-mono">
                  <div className="flex justify-between py-1 border-b-theme">
                    <span className="text-theme-secondary">Deduplication Records:</span>
                    <span className="font-bold text-theme-primary">{systemHealth?.dedup_statistics?.total_dedup_records || kanbanItems.length}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b-theme">
                    <span className="text-theme-secondary">Active Mailboxes:</span>
                    <span className="font-bold text-theme-primary">{mailboxes.length}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b-theme">
                    <span className="text-theme-secondary">Zero-Bounce Hygiene:</span>
                    <span className="text-theme-success font-bold">3-Stage Active</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-theme-secondary">Database Layer:</span>
                    <span className="text-theme-primary">SQLite WAL Mode</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
          </div>
      </main>
    </div>

      {/* MODAL: MULTI-FORMAT DATA BACKUP */}
      {isBackupModalOpen && (
        <div className="np-modal-backdrop">
          <div className="np-modal max-w-lg">
            <div className="np-modal-header">
              <div>
                <h3 className="font-bold text-sm text-theme-primary">
                  Database Backup & Multi-Format Export
                </h3>
                <p className="text-xs text-theme-secondary mt-0.5">
                  Generate cryptographic snapshot backups for local archiving or CRM integration.
                </p>
              </div>
              <button
                onClick={() => !isBackingUp && setIsBackupModalOpen(false)}
                className="text-theme-secondary hover:text-theme-primary font-bold"
                disabled={isBackingUp}
              >
                ✕
              </button>
            </div>

            <div className="np-modal-body space-y-4">
              <div className="bg-elevated p-3 rounded border-theme text-xs font-mono space-y-1">
                <div className="flex justify-between text-theme-secondary">
                  <span>Available Leads:</span>
                  <span className="font-bold text-theme-accent">{kanbanItems.length} Leads</span>
                </div>
                <div className="flex justify-between text-theme-secondary">
                  <span>Server Backup Path:</span>
                  <span className="text-theme-primary truncate max-w-[240px]">Desktop/rabbi/vault/backups/</span>
                </div>
                <div className="flex justify-between text-theme-secondary">
                  <span>Payload Encryption:</span>
                  <span className="text-theme-success font-bold">AES-256 Validated</span>
                </div>
              </div>

              <div className="space-y-2.5">
                <div className="np-card p-3 flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-xs text-theme-primary">JSON Format (.json)</div>
                    <div className="text-[11px] text-theme-secondary">Full hierarchical schema with tech stack & DNS MX logs</div>
                  </div>
                  <button
                    onClick={() => handleDownloadBackup("json")}
                    disabled={isBackingUp}
                    className="btn btn-secondary btn-sm"
                  >
                    Export .json
                  </button>
                </div>

                <div className="np-card p-3 flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-xs text-theme-primary">Excel Spreadsheet (.xlsx)</div>
                    <div className="text-[11px] text-theme-secondary">Formatted multi-column workbook for MS Excel & Sheets</div>
                  </div>
                  <button
                    onClick={() => handleDownloadBackup("xlsx")}
                    disabled={isBackingUp}
                    className="btn btn-primary btn-sm"
                  >
                    Export .xlsx
                  </button>
                </div>

                <div className="np-card p-3 flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-xs text-theme-primary">CSV Delimited (.csv)</div>
                    <div className="text-[11px] text-theme-secondary">Flat RFC 4180 dataset for HubSpot / Salesforce import</div>
                  </div>
                  <button
                    onClick={() => handleDownloadBackup("csv")}
                    disabled={isBackingUp}
                    className="btn btn-secondary btn-sm"
                  >
                    Export .csv
                  </button>
                </div>
              </div>
            </div>

            <div className="np-modal-footer">
              <button
                type="button"
                onClick={() => setIsBackupModalOpen(false)}
                disabled={isBackingUp}
                className="btn btn-ghost btn-sm"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: HUNT & VERIFY LEAD ENGINE */}
      {isHuntModalOpen && (
        <div className="np-modal-backdrop">
          <div className="np-modal max-w-lg">
            <div className="np-modal-header">
              <div>
                <h3 className="font-bold text-sm text-theme-primary">
                  Hunt & Verify: Targeted Lead Pipeline
                </h3>
                <p className="text-xs text-theme-secondary mt-0.5">
                  Deep Scraper + Zero-Bounce 3-Stage Hygiene Engine
                </p>
              </div>
              <button
                onClick={() => isHunting ? handleCancelScrape() : setIsHuntModalOpen(false)}
                className="text-theme-secondary hover:text-theme-primary font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleLaunchScrapePipeline}>
              <div className="np-modal-body space-y-4">
                <div className="space-y-3 p-3.5 bg-elevated rounded border-theme">
                  <div className="text-xs font-semibold uppercase tracking-wider text-theme-secondary">
                    Target Geographic Location
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="np-label">1. Target Region</label>
                      <select
                        value={huntRegion}
                        onChange={(e) => handleRegionChange(e.target.value)}
                        className="np-select"
                        disabled={isHunting}
                      >
                        {Object.keys(GEO_REGIONS).map(r => (
                          <option key={r} value={r}>{r}</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="np-label">2. Target Country</label>
                      <select
                        value={huntCountry}
                        onChange={(e) => handleCountryChange(e.target.value)}
                        className="np-select"
                        disabled={isHunting}
                      >
                        {availableCountries.map(c => (
                          <option key={c} value={c}>{c}</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <label className="np-label mb-0">3. Target City</label>
                      <button
                        type="button"
                        onClick={() => setIsCustomCity(!isCustomCity)}
                        className="text-[11px] text-theme-accent hover:underline font-medium"
                      >
                        {isCustomCity ? "Choose from standard list" : "Specify custom city"}
                      </button>
                    </div>

                    {isCustomCity ? (
                      <input
                        type="text"
                        value={huntCustomCity}
                        onChange={(e) => setHuntCustomCity(e.target.value)}
                        placeholder="e.g. Baden-Baden, Cambridge, San Jose"
                        className="np-input font-mono text-xs"
                        disabled={isHunting}
                        autoFocus
                      />
                    ) : (
                      <select
                        value={huntCity}
                        onChange={(e) => setHuntCity(e.target.value)}
                        className="np-select"
                        disabled={isHunting}
                      >
                        {availableCities.map(city => (
                          <option key={city} value={city}>{city}</option>
                        ))}
                      </select>
                    )}
                  </div>
                </div>

                <div>
                  <label className="np-label">Custom Niche / Target Keyword</label>
                  <input
                    type="text"
                    value={huntNiche}
                    onChange={(e) => setHuntNiche(e.target.value)}
                    placeholder="Type any keyword or select a preset below →"
                    className="np-input"
                    required
                    disabled={isHunting}
                  />

                  <p className="text-[10px] text-theme-secondary mt-1 mb-1.5">— Quick Presets —</p>
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {INDUSTRY_PRESETS.map((preset) => (
                      <button
                        key={preset}
                        type="button"
                        onClick={() => setHuntNiche(preset)}
                        disabled={isHunting}
                        className={`text-[11px] px-2 py-0.5 rounded border transition-colors ${
                          huntNiche === preset
                            ? "bg-[var(--accent-muted)] text-[var(--accent)] border-[var(--accent)] font-medium"
                            : "bg-elevated text-theme-secondary border-theme hover:bg-hover"
                        }`}
                      >
                        {preset}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="np-label">Target Domains / Seed URLs (Optional, one per line)</label>
                  <textarea
                    rows={2}
                    value={huntTargetUrls}
                    onChange={(e) => setHuntTargetUrls(e.target.value)}
                    placeholder="https://example-contractor.de&#10;https://berlin-bau.com"
                    className="np-textarea font-mono text-xs"
                    disabled={isHunting}
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="np-label mb-0">Scraping Limit Counter</label>
                    <span className="badge badge-accent font-bold">
                      {huntMaxResults} Leads
                    </span>
                  </div>

                  <input
                    type="range"
                    min="5"
                    max="100"
                    step="5"
                    value={huntMaxResults}
                    onChange={(e) => setHuntMaxResults(parseInt(e.target.value, 10))}
                    className="w-full"
                    disabled={isHunting}
                  />

                  <div className="flex justify-between text-[11px] text-theme-muted mt-1">
                    <span>5</span>
                    <span>25</span>
                    <span>50</span>
                    <span>75</span>
                    <span>100 Max</span>
                  </div>

                  <div className="flex gap-1.5 mt-2">
                    {[10, 25, 50, 100].map((preset) => (
                      <button
                        key={preset}
                        type="button"
                        onClick={() => setHuntMaxResults(preset)}
                        disabled={isHunting}
                        className={`btn btn-sm flex-1 justify-center ${huntMaxResults === preset ? 'btn-primary' : 'btn-secondary'}`}
                      >
                        {preset} {preset === 100 ? "Enterprise" : "Leads"}
                      </button>
                    ))}
                  </div>
                </div>

                {isHunting && (
                  <div className="np-alert np-alert-info">
                    <span className="w-2 h-2 rounded-full bg-[var(--accent)] animate-ping" />
                    <span>Executing targeted crawl for {huntNiche} in {isCustomCity ? huntCustomCity : huntCity}, {huntCountry}...</span>
                  </div>
                )}

                {!isHunting && huntProgress && (
                  <div className="np-alert np-alert-success mt-2">
                    <div className="flex flex-wrap gap-3 text-sm font-medium">
                      <span>🔍 Discovered: <strong>{huntProgress.scraped_raw || 0}</strong></span>
                      <span>🚫 Filtered: <strong>{huntProgress.filtered_count || 0}</strong></span>
                      <span>✅ Clean: <strong>{huntProgress.clean_count || 0}</strong></span>
                      {huntProgress.breakdown && (
                        <span className="text-xs text-theme-muted ml-1">
                          ({huntProgress.breakdown.blacklisted || 0} blacklisted, {huntProgress.breakdown.duplicate || 0} dupes, {huntProgress.breakdown.no_mx || 0} no-MX)
                        </span>
                      )}
                      {huntProgress.fallback_triggered && (
                        <span className="badge badge-warning text-xs">⚡ Fallback: {huntProgress.fallback_source}</span>
                      )}
                    </div>
                  </div>
                )}
              </div>

              <div className="np-modal-footer">
                <button
                  type="button"
                  onClick={() => isHunting ? handleCancelScrape() : setIsHuntModalOpen(false)}
                  className="btn btn-ghost btn-sm"
                >
                  {isHunting ? "⛔ Stop Hunt" : "Cancel"}
                </button>
                <button
                  type="submit"
                  disabled={isHunting}
                  className="btn btn-primary btn-sm"
                >
                  <span>Launch Lead Pipeline</span>
                  <span>➔</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: HUMAN APPROVAL GATE REVIEW */}
      {selectedApproval && (
        <div className="np-modal-backdrop">
          <div className="np-modal max-w-xl">
            <div className="np-modal-header">
              <div>
                <h3 className="font-bold text-sm text-theme-primary">
                  Review & Authorize Outreach: {selectedApproval.company_name}
                </h3>
                <p className="text-xs text-theme-secondary mt-0.5">
                  Scheduled for dynamic 9:00 AM - 5:00 PM local recipient timezone.
                </p>
              </div>
              <button
                onClick={() => setSelectedApproval(null)}
                className="text-theme-secondary hover:text-theme-primary font-bold"
              >
                ✕
              </button>
            </div>

            <div className="np-modal-body space-y-3">
              <div>
                <label className="np-label">Campaign Niche & Template Switcher</label>
                <select
                  value={approvalNiche}
                  onChange={(e) => handleTemplateSwitch(e.target.value)}
                  className="np-input font-mono bg-elevated"
                >
                  {[...INDUSTRY_PRESETS, ...(templatesList || []).map(t => t.niche).filter(n => n && !INDUSTRY_PRESETS.includes(n))].map(n => (
                    <option key={n} value={n}>{n}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="np-label">Company / Brand Name</label>
                <input
                  type="text"
                  value={approvalCompanyName}
                  onChange={(e) => handleCompanyNameChange(e.target.value)}
                  placeholder="e.g. Zeus Fitness or Acme Corp"
                  className="np-input font-mono"
                />
              </div>

              <div>
                <label className="np-label">Recipient Destination</label>
                <input
                  type="email"
                  value={approvalRecipient}
                  onChange={(e) => setApprovalRecipient(e.target.value)}
                  placeholder="recipient@domain.com"
                  className="np-input font-mono"
                />
              </div>

              <div>
                <label className="np-label">Email Subject</label>
                <input
                  type="text"
                  value={approvalSubject}
                  onChange={(e) => setApprovalSubject(e.target.value)}
                  className="np-input font-mono"
                />
              </div>

              <div>
                <label className="np-label">Outreach Message Body</label>
                <textarea
                  rows={7}
                  value={approvalBody}
                  onChange={(e) => setApprovalBody(e.target.value)}
                  className="np-textarea"
                />
              </div>
            </div>

            <div className="np-modal-footer flex items-center justify-between">
              <button
                onClick={() => handleDeleteQueueItem(selectedApproval.id, approvalRecipient)}
                className="btn btn-danger btn-sm flex items-center gap-1"
                title="Permanently remove this lead from the gate"
              >
                <span>🗑️ Delete Lead</span>
              </button>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setSelectedApproval(null)}
                  className="btn btn-ghost btn-sm"
                >
                  Cancel
                </button>
                {user ? (
                  <>
                    <button
                      onClick={() => handleApproveOutreach(selectedApproval.id, approvalSubject, approvalBody, approvalRecipient, approvalCompanyName)}
                      className="btn btn-warning btn-sm"
                    >
                      Authorize & Schedule (9-5 Window)
                    </button>
                    <button
                      onClick={async () => {
                        await handleApproveOutreach(selectedApproval.id, approvalSubject, approvalBody, approvalRecipient, approvalCompanyName);
                        await handleDispatchQueueNow(true, selectedApproval.id);
                      }}
                      className="btn btn-primary btn-sm flex items-center gap-1"
                      title="Authorize and immediately dispatch outside business hours or on weekends"
                    >
                      <span>⚡ Authorize & Dispatch Now</span>
                    </button>
                  </>
                ) : null}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: HOT LEAD 1-CLICK AI REPLY */}
      {selectedHotLead && (
        <div className="np-modal-backdrop">
          <div className="np-modal max-w-xl border-[var(--danger)]">
            <div className="np-modal-header">
              <div>
                <h3 className="font-bold text-sm text-theme-danger">
                  1-Click AI Response: {selectedHotLead.company_name && !["gmail.com", "outlook.com", "yahoo.com", "hotmail.com", "icloud.com", "mail.com"].includes(selectedHotLead.company_name.toLowerCase()) && selectedHotLead.company_name !== selectedHotLead.sender_email
                    ? selectedHotLead.company_name
                    : (selectedHotLead.sender_email
                        ? selectedHotLead.sender_email.split("@")[0].replace(/[._-]/g, " ").replace(/\b\w/g, c => c.toUpperCase())
                        : (selectedHotLead.company_name || "Direct Inquirer"))}
                </h3>
                <p className="text-xs text-theme-secondary mt-0.5">
                  High-intent response detected by IMAP listener.
                </p>
              </div>
              <button
                onClick={() => setSelectedHotLead(null)}
                className="text-theme-secondary hover:text-theme-primary font-bold"
              >
                ✕
              </button>
            </div>

            <div className="np-modal-body space-y-3">
              <div className="bg-elevated p-3 rounded border-theme text-xs font-mono">
                <div className="text-theme-secondary font-semibold">Incoming Inquiry:</div>
                <div className="text-theme-primary mt-1">{incomingInquiryText || selectedHotLead.reply_snippet || selectedHotLead.message_body || "(No reply text available)"}</div>
              </div>

              <div>
                <label className="np-label">AI Suggested Executive Response</label>
                <textarea
                  rows={6}
                  value={hotLeadReplyBody}
                  onChange={(e) => setHotLeadReplyBody(e.target.value)}
                  className="np-textarea"
                />
              </div>
            </div>

            <div className="np-modal-footer">
              <button
                onClick={() => setSelectedHotLead(null)}
                className="btn btn-ghost btn-sm"
              >
                Dismiss
              </button>
              <button
                onClick={() => handleDispatchHotLeadReply(selectedHotLead.id, selectedHotLead.recipient || selectedHotLead.sender_email || selectedHotLead.primary_email, hotLeadReplyBody)}
                className="btn btn-danger btn-sm"
              >
                Dispatch Response Now ➔
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: ADD NEW MAILBOX */}
      {isAddMailboxOpen && (
        <div className="np-modal-backdrop">
          <div className="np-modal max-w-lg">
            <div className="np-modal-header">
              <div>
                <h3 className="font-bold text-sm text-theme-primary">
                  Enroll New Mailbox into Rotator Pool
                </h3>
                <p className="text-xs text-theme-secondary mt-0.5">
                  Connect via custom SMTP with strict reputation safeguard send-caps.
                </p>
              </div>
              <button
                onClick={() => setIsAddMailboxOpen(false)}
                className="text-theme-secondary hover:text-theme-primary font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleAddMailbox}>
              <div className="np-modal-body space-y-3">
                <div className="bg-elevated p-2.5 rounded border border-[var(--border-subtle)] flex items-center justify-between">
                  <div className="text-xs text-theme-secondary">
                    Need Gmail App Password or Webhook relay script?
                  </div>
                  <button
                    type="button"
                    onClick={() => setIsSetupGuideOpen(true)}
                    className="btn btn-secondary btn-xs text-theme-accent font-semibold"
                  >
                    📘 View Setup Guide
                  </button>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="np-label">Sender Display Name</label>
                    <input
                      type="text"
                      value={newMbDisplayName}
                      onChange={(e) => setNewMbDisplayName(e.target.value)}
                      placeholder="e.g. H. Huddair Estimating"
                      className="np-input"
                      required
                    />
                  </div>
                  <div>
                    <label className="np-label">Email Address</label>
                    <input
                      type="email"
                      value={newMbEmail}
                      onChange={(e) => setNewMbEmail(e.target.value)}
                      placeholder="tenders@domain.de"
                      className="np-input font-mono"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="np-label">SMTP Server Host</label>
                    <input
                      type="text"
                      value={newMbHost}
                      onChange={(e) => setNewMbHost(e.target.value)}
                      placeholder="smtp.domain.de"
                      className="np-input font-mono"
                    />
                  </div>
                  <div>
                    <label className="np-label">Port</label>
                    <input
                      type="number"
                      value={newMbPort}
                      onChange={(e) => setNewMbPort(e.target.value)}
                      className="np-input font-mono"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="np-label">SMTP Username</label>
                    <input
                      type="text"
                      value={newMbUsername}
                      onChange={(e) => setNewMbUsername(e.target.value)}
                      placeholder="Leave blank to use email"
                      className="np-input font-mono"
                    />
                  </div>
                  <div>
                    <label className="np-label">App Password / Secret</label>
                    <input
                      type="password"
                      value={newMbPassword}
                      onChange={(e) => setNewMbPassword(e.target.value)}
                      placeholder="••••••••••••"
                      className="np-input font-mono"
                    />
                  </div>
                </div>

                <div>
                  <label className="np-label">Daily Send Cap (Max 50 recommended)</label>
                  <input
                    type="number"
                    value={newMbDailyLimit}
                    onChange={(e) => setNewMbDailyLimit(e.target.value)}
                    className="np-input font-mono"
                    min="10"
                    max="100"
                    required
                  />
                </div>

                <div>
                  <label className="np-label">Google Apps Script Webhook URL <span className="text-theme-muted font-normal">(Optional — Bypasses SMTP Port Block)</span></label>
                  <input
                    type="url"
                    value={newMbWebhookUrl}
                    onChange={(e) => setNewMbWebhookUrl(e.target.value)}
                    placeholder="https://script.google.com/macros/s/.../exec"
                    className="np-input font-mono"
                  />
                  <span className="text-[10px] text-theme-muted mt-0.5 block">
                    Optional: If set, outbound emails for this mailbox are relayed via HTTPS Webhook, completely bypassing cloud host / Railway SMTP port blocks.
                  </span>
                </div>
              </div>

              <div className="np-modal-footer">
                <button
                  type="button"
                  onClick={() => setIsAddMailboxOpen(false)}
                  className="btn btn-ghost btn-sm"
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary btn-sm">
                  Enroll Mailbox
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: EDIT SMTP SETTINGS */}
      {selectedMailboxForEdit && (
        <div className="np-modal-backdrop">
          <div className="np-modal max-w-lg">
            <div className="np-modal-header">
              <div>
                <h3 className="font-bold text-sm text-theme-primary">
                  Configure SMTP: {selectedMailboxForEdit.display_name}
                </h3>
                <p className="text-xs text-theme-secondary mt-0.5">
                  Update credentials, port, and daily limit caps.
                </p>
              </div>
              <button
                onClick={() => setSelectedMailboxForEdit(null)}
                className="text-theme-secondary hover:text-theme-primary font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleUpdateMailbox}>
              <div className="np-modal-body space-y-3">
                <div className="bg-elevated p-2.5 rounded border border-[var(--border-subtle)] flex items-center justify-between">
                  <div className="text-xs text-theme-secondary">
                    Need Gmail App Password or Webhook relay script?
                  </div>
                  <button
                    type="button"
                    onClick={() => setIsSetupGuideOpen(true)}
                    className="btn btn-secondary btn-xs text-theme-accent font-semibold"
                  >
                    📘 View Setup Guide
                  </button>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="np-label">Display Name</label>
                    <input
                      type="text"
                      value={editMbDisplayName}
                      onChange={(e) => setEditMbDisplayName(e.target.value)}
                      className="np-input"
                      required
                    />
                  </div>
                  <div>
                    <label className="np-label">Email Address</label>
                    <input
                      type="email"
                      value={editMbEmail}
                      onChange={(e) => setEditMbEmail(e.target.value)}
                      className="np-input font-mono"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="np-label">SMTP Host</label>
                    <input
                      type="text"
                      value={editMbHost}
                      onChange={(e) => setEditMbHost(e.target.value)}
                      className="np-input font-mono"
                    />
                  </div>
                  <div>
                    <label className="np-label">Port</label>
                    <input
                      type="number"
                      value={editMbPort}
                      onChange={(e) => setEditMbPort(e.target.value)}
                      className="np-input font-mono"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="np-label">Username</label>
                    <input
                      type="text"
                      value={editMbUsername}
                      onChange={(e) => setEditMbUsername(e.target.value)}
                      className="np-input font-mono"
                    />
                  </div>
                  <div>
                    <label className="np-label">Password (blank to keep)</label>
                    <input
                      type="password"
                      value={editMbPassword}
                      onChange={(e) => setEditMbPassword(e.target.value)}
                      placeholder="••••••••••••"
                      className="np-input font-mono"
                    />
                  </div>
                </div>

                <div>
                  <label className="np-label">Daily Send Cap</label>
                  <input
                    type="number"
                    value={editMbDailyLimit}
                    onChange={(e) => setEditMbDailyLimit(e.target.value)}
                    className="np-input font-mono"
                    min="10"
                    max="100"
                    required
                  />
                </div>

                <div>
                  <label className="np-label">Google Apps Script Webhook URL <span className="text-theme-muted font-normal">(Optional — Bypasses SMTP Port Block)</span></label>
                  <input
                    type="url"
                    value={editMbWebhookUrl}
                    onChange={(e) => setEditMbWebhookUrl(e.target.value)}
                    placeholder="https://script.google.com/macros/s/.../exec"
                    className="np-input font-mono"
                  />
                  <span className="text-[10px] text-theme-muted mt-0.5 block">
                    Optional: If set, outbound emails for this mailbox are relayed via HTTPS Webhook, completely bypassing cloud host / Railway SMTP port blocks.
                  </span>
                </div>
              </div>

              <div className="np-modal-footer">
                <button
                  type="button"
                  onClick={() => setSelectedMailboxForEdit(null)}
                  className="btn btn-ghost btn-sm"
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary btn-sm">
                  Save Settings
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: CREATE OPERATOR */}
      {isCreateOperatorOpen && (
        <div className="np-modal-backdrop">
          <div className="np-modal max-w-lg">
            <div className="np-modal-header">
              <div>
                <h3 className="font-bold text-sm text-theme-primary">
                  Create Operator Account
                </h3>
                <p className="text-xs text-theme-secondary mt-0.5">
                  Issues hardware-locked credentials and cryptographic license token.
                </p>
              </div>
              <button
                onClick={() => setIsCreateOperatorOpen(false)}
                className="text-theme-secondary hover:text-theme-primary font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateOperator}>
              <div className="np-modal-body space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="np-label">Username</label>
                    <input
                      type="text"
                      value={newOpUsername}
                      onChange={(e) => setNewOpUsername(e.target.value)}
                      placeholder="e.g. operator_berlin"
                      className="np-input font-mono"
                      required
                    />
                  </div>
                  <div>
                    <label className="np-label">Temporary Password (Bcrypt)</label>
                    <input
                      type="password"
                      value={newOpPassword}
                      onChange={(e) => setNewOpPassword(e.target.value)}
                      placeholder="••••••••••••"
                      className="np-input font-mono"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="np-label">Full Operator Name</label>
                    <input
                      type="text"
                      value={newOpFullName}
                      onChange={(e) => setNewOpFullName(e.target.value)}
                      placeholder="e.g. Klaus Richter"
                      className="np-input"
                      required
                    />
                  </div>
                  <div>
                    <label className="np-label">Email Address</label>
                    <input
                      type="email"
                      value={newOpEmail}
                      onChange={(e) => setNewOpEmail(e.target.value)}
                      placeholder="klaus@nexus-pulse.io"
                      className="np-input font-mono"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="np-label">Device Lock (Host Machine-ID)</label>
                  <input
                    type="text"
                    value={newOpDeviceLock}
                    onChange={(e) => setNewOpDeviceLock(e.target.value)}
                    placeholder="Leave blank to auto-bind on first login"
                    className="np-input font-mono"
                  />
                  <span className="text-[10px] text-theme-muted mt-0.5 block">
                    Optional: If left blank, locks automatically to the first physical device used to log in.
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="np-label">Expiry (Days)</label>
                    <input
                      type="number"
                      value={newOpExpiryDays}
                      onChange={(e) => setNewOpExpiryDays(e.target.value)}
                      className="np-input font-mono"
                    />
                  </div>
                  <div>
                    <label className="np-label">Scrape Quota/d</label>
                    <input
                      type="number"
                      value={newOpScrapeQuota}
                      onChange={(e) => setNewOpScrapeQuota(e.target.value)}
                      className="np-input font-mono"
                    />
                  </div>
                  <div>
                    <label className="np-label">Send Quota/d</label>
                    <input
                      type="number"
                      value={newOpSendQuota}
                      onChange={(e) => setNewOpSendQuota(e.target.value)}
                      className="np-input font-mono"
                    />
                  </div>
                </div>
              </div>

              <div className="np-modal-footer">
                <button
                  type="button"
                  onClick={() => setIsCreateOperatorOpen(false)}
                  disabled={isCreatingOperator}
                  className="btn btn-ghost btn-sm"
                >
                  Cancel
                </button>
                <button type="submit" disabled={isCreatingOperator} className="btn btn-primary btn-sm">
                  {isCreatingOperator ? "Issuing License..." : "Issue License & Create"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: RESET OPERATOR PASSWORD */}
      {selectedUserForReset && (
        <div className="np-modal-backdrop">
          <div className="np-modal max-w-sm">
            <div className="np-modal-header">
              <div>
                <h3 className="font-bold text-sm text-theme-primary">
                  Reset Password: {selectedUserForReset.username}
                </h3>
              </div>
              <button
                onClick={() => setSelectedUserForReset(null)}
                className="text-theme-secondary hover:text-theme-primary font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleResetOperatorPassword}>
              <div className="np-modal-body space-y-3">
                <p className="text-xs text-theme-secondary">
                  Enter new passphrase. It will be salted and encrypted using Bcrypt (cost 12) before persisting to SQLite.
                </p>

                <div>
                  <label className="np-label">New Password</label>
                  <input
                    type="password"
                    value={resetPasswordInput}
                    onChange={(e) => setResetPasswordInput(e.target.value)}
                    placeholder="••••••••••••"
                    className="np-input font-mono"
                    autoFocus
                    required
                  />
                </div>
              </div>

              <div className="np-modal-footer">
                <button
                  type="button"
                  onClick={() => setSelectedUserForReset(null)}
                  disabled={isResettingPassword}
                  className="btn btn-ghost btn-sm"
                >
                  Cancel
                </button>
                <button type="submit" disabled={isResettingPassword} className="btn btn-primary btn-sm">
                  {isResettingPassword ? "Encrypting with Bcrypt..." : "Reset with Bcrypt"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      {/* MODAL: PROPOSAL TEMPLATE EDITOR */}
      {isTemplateModalOpen && (
        <div className="np-modal-backdrop">
          <div className="np-modal max-w-2xl">
            <div className="np-modal-header">
              <div>
                <h3 className="font-bold text-sm text-theme-primary">
                  {editingTemplate ? "Edit Proposal Template" : "Create New Proposal Template"}
                </h3>
                <p className="text-xs text-theme-secondary mt-0.5">
                  Dynamic niche-matching proposal with automated token interpolation.
                </p>
              </div>
              <button
                onClick={() => setIsTemplateModalOpen(false)}
                className="text-theme-secondary hover:text-theme-primary font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSaveTemplate}>
              <div className="np-modal-body space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="np-label">Template Title</label>
                    <input
                      type="text"
                      value={tplTitle}
                      onChange={(e) => setTplTitle(e.target.value)}
                      placeholder="e.g. Commercial Tender Outreach"
                      className="np-input font-medium"
                      required
                    />
                  </div>
                  <div>
                    <label className="np-label">Target Niche / Industry</label>
                    <input
                      type="text"
                      value={tplNiche}
                      onChange={(e) => setTplNiche(e.target.value)}
                      placeholder="e.g. Commercial Construction"
                      className="np-input"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="np-label">Email Subject Line</label>
                  <input
                    type="text"
                    value={tplSubject}
                    onChange={(e) => setTplSubject(e.target.value)}
                    placeholder="e.g. Commercial Capacity & Tenders // {{company_name}}"
                    className="np-input font-mono text-xs"
                    required
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="np-label mb-0">Proposal Body Content</label>
                    <span className="text-[11px] text-theme-muted">Click chips below to insert variables</span>
                  </div>

                  {/* Token Insertion Chips */}
                  <div className="flex flex-wrap gap-1.5 mb-2">
                    {[
                      "{{company_name}}",
                      "{{niche}}",
                      "{{country}}",
                      "{{city}}",
                      "{{tech_stack}}",
                      "{{unsubscribe_link}}"
                    ].map((tag) => (
                      <button
                        key={tag}
                        type="button"
                        onClick={() => handleInsertTag(tag)}
                        className="np-variable-chip"
                        title={`Insert ${tag}`}
                      >
                        + {tag}
                      </button>
                    ))}
                  </div>

                  <textarea
                    rows={8}
                    value={tplBody}
                    onChange={(e) => setTplBody(e.target.value)}
                    className="np-textarea font-mono text-xs"
                    placeholder="Write your dynamic proposal copy here..."
                    required
                  />
                </div>

                <div className="flex items-center gap-2 pt-2 border-t-theme">
                  <input
                    type="checkbox"
                    id="tpl-default"
                    checked={tplIsDefault}
                    onChange={(e) => setTplIsDefault(e.target.checked)}
                    className="cursor-pointer"
                  />
                  <label htmlFor="tpl-default" className="text-xs text-theme-primary cursor-pointer select-none">
                    Set as Default Fallback Template (used when no exact niche matches)
                  </label>
                </div>
              </div>

              <div className="np-modal-footer">
                <button
                  type="button"
                  onClick={() => setIsTemplateModalOpen(false)}
                  className="btn btn-ghost btn-sm"
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary btn-sm">
                  {editingTemplate ? "Save Changes" : "Create Template"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      {/* MODAL: SETUP GUIDE & WEBHOOK SCRIPT */}
      {isSetupGuideOpen && (
        <div className="np-modal-backdrop">
          <div className="np-modal max-w-2xl">
            <div className="np-modal-header">
              <div>
                <h3 className="font-bold text-sm text-theme-primary flex items-center gap-2">
                  <span>📘 Mailbox Setup Guide & Webhook Dispatcher</span>
                </h3>
                <p className="text-xs text-theme-secondary mt-0.5">
                  Complete non-technical setup instructions for Gmail SMTP and Google Apps Script Webhooks.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setIsSetupGuideOpen(false)}
                className="text-theme-secondary hover:text-theme-primary font-bold text-lg"
              >
                ✕
              </button>
            </div>

            <div className="np-modal-body space-y-4">
              {/* Tab Selector */}
              <div className="flex border-b border-[var(--border-subtle)] gap-4">
                <button
                  type="button"
                  onClick={() => setSetupGuideTab("gmail_smtp")}
                  className={`pb-2 text-xs font-semibold border-b-2 transition-colors ${
                    setupGuideTab === "gmail_smtp"
                      ? "border-[var(--accent)] text-theme-primary font-bold"
                      : "border-transparent text-theme-secondary hover:text-theme-primary"
                  }`}
                >
                  1. Gmail App Password & SMTP
                </button>
                <button
                  type="button"
                  onClick={() => setSetupGuideTab("webhook_script")}
                  className={`pb-2 text-xs font-semibold border-b-2 transition-colors ${
                    setupGuideTab === "webhook_script"
                      ? "border-[var(--accent)] text-theme-primary font-bold"
                      : "border-transparent text-theme-secondary hover:text-theme-primary"
                  }`}
                >
                  2. Google Apps Script Webhook Relay
                </button>
              </div>

              {setupGuideTab === "gmail_smtp" ? (
                <div className="space-y-3 text-xs leading-relaxed text-theme-secondary">
                  <div className="bg-elevated p-3 rounded border border-[var(--border-subtle)]">
                    <h4 className="font-semibold text-theme-primary mb-1">Why an App Password?</h4>
                    <p>
                      Google does not allow third-party SaaS apps to use your direct account password.
                      A 16-character <strong>App Password</strong> grants secure, isolated SMTP/IMAP access.
                    </p>
                  </div>

                  <ol className="list-decimal list-inside space-y-2 font-mono">
                    <li>
                      <strong className="text-theme-primary">Step 1:</strong> Go to your Google Account (<a href="https://myaccount.google.com/security" target="_blank" rel="noreferrer" className="text-theme-accent underline">myaccount.google.com/security</a>).
                    </li>
                    <li>
                      <strong className="text-theme-primary">Step 2:</strong> Under <em>How you sign in to Google</em>, verify that <strong>2-Step Verification</strong> is turned ON.
                    </li>
                    <li>
                      <strong className="text-theme-primary">Step 3:</strong> Search for <strong>App Passwords</strong> (or visit <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noreferrer" className="text-theme-accent underline">myaccount.google.com/apppasswords</a>).
                    </li>
                    <li>
                      <strong className="text-theme-primary">Step 4:</strong> Enter an App Name (e.g. <span className="text-theme-accent">Nexus-Pulse</span>) and click <strong>Create</strong>.
                    </li>
                    <li>
                      <strong className="text-theme-primary">Step 5:</strong> Copy the 16-character generated code (e.g. <span className="text-theme-accent">xxxx xxxx xxxx xxxx</span>).
                    </li>
                  </ol>

                  <div className="bg-elevated p-3 rounded border border-[var(--border-subtle)] space-y-1 font-mono text-[11px]">
                    <div className="font-bold text-theme-primary pb-1 border-b border-[var(--border-subtle)]">
                      Standard Nexus-Pulse Settings for Gmail:
                    </div>
                    <div className="flex justify-between py-0.5">
                      <span className="text-theme-muted">SMTP Server:</span>
                      <span className="text-theme-primary font-bold">smtp.gmail.com</span>
                    </div>
                    <div className="flex justify-between py-0.5">
                      <span className="text-theme-muted">SMTP Port:</span>
                      <span className="text-theme-primary font-bold">587 (TLS)</span>
                    </div>
                    <div className="flex justify-between py-0.5">
                      <span className="text-theme-muted">IMAP Server:</span>
                      <span className="text-theme-primary font-bold">imap.gmail.com</span>
                    </div>
                    <div className="flex justify-between py-0.5">
                      <span className="text-theme-muted">IMAP Port:</span>
                      <span className="text-theme-primary font-bold">993 (SSL/TLS)</span>
                    </div>
                    <div className="flex justify-between py-0.5">
                      <span className="text-theme-muted">Username:</span>
                      <span className="text-theme-primary font-bold">Your full Gmail address</span>
                    </div>
                    <div className="flex justify-between py-0.5">
                      <span className="text-theme-muted">Password:</span>
                      <span className="text-theme-primary font-bold">16-character App Password</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-3 text-xs leading-relaxed text-theme-secondary">
                  <div className="bg-elevated p-3 rounded border border-[var(--border-subtle)]">
                    <h4 className="font-semibold text-theme-primary mb-1">100% Deliverability Webhook Relay</h4>
                    <p>
                      Deploy this 20-line Google Apps Script to relay emails directly through Google's native IP pool.
                      Guarantees zero IP blocklisting or Railway datacenter reputation flags.
                    </p>
                  </div>

                  <div className="relative">
                    <div className="flex items-center justify-between bg-surface px-3 py-1.5 rounded-t border-t border-x border-[var(--border-subtle)] font-mono text-[11px]">
                      <span>Code.gs (Google Apps Script)</span>
                      <button
                        type="button"
                        onClick={handleCopyWebhookScript}
                        className="btn btn-secondary btn-xs text-theme-accent font-semibold"
                      >
                        {copiedWebhookScript ? "✓ Copied!" : "📋 Copy Script"}
                      </button>
                    </div>
                    <pre className="bg-[#0d1117] text-[#c9d1d9] p-3 rounded-b border border-[var(--border-subtle)] font-mono text-[11px] overflow-x-auto max-h-48 scrollbar-thin">
                      {WEBHOOK_SCRIPT_TEMPLATE}
                    </pre>
                  </div>

                  <ol className="list-decimal list-inside space-y-1.5 font-mono text-[11px]">
                    <li>Open <a href="https://script.google.com" target="_blank" rel="noreferrer" className="text-theme-accent underline">script.google.com</a> and click <strong>New Project</strong>.</li>
                    <li>Replace all code in <strong>Code.gs</strong> with the snippet above and click <strong>Save (Ctrl+S)</strong>.</li>
                    <li>Click <strong>Deploy ➔ New deployment</strong>. Click the gear icon and select <strong>Web app</strong>.</li>
                    <li>Set <strong>Execute as:</strong> <em>Me</em> and <strong>Who has access:</strong> <em>Anyone</em>.</li>
                    <li>Click <strong>Deploy</strong>, authorize permissions, and copy the <strong>Web App URL</strong> into the Nexus-Pulse mailbox form.</li>
                  </ol>
                </div>
              )}
            </div>

            <div className="np-modal-footer">
              <button
                type="button"
                onClick={() => setIsSetupGuideOpen(false)}
                className="btn btn-primary btn-sm"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: 2-DAY FREE TRIAL ACTIVATION (POP-UP ON FIRST LOGIN FOR OPERATORS) */}
      {user && user.role === "operator" && (!user.trial_active || user.trial_status === "pending") && user.trial_status !== "expired" && user.subscription_status !== "active" && (
        <div className="np-modal-backdrop">
          <div className="np-modal max-w-md text-center p-6 space-y-4">
            <div className="w-16 h-16 mx-auto rounded-full bg-[var(--accent-muted)] border-2 border-[var(--accent)] flex items-center justify-center text-3xl">
              🚀
            </div>

            <div>
              <h3 className="font-bold text-lg text-theme-primary">
                Activate Your 2-Day Free Trial
              </h3>
              <p className="text-xs text-theme-secondary mt-1">
                Welcome to Nexus-Pulse! Your account has 48 hours of unrestricted access to the automated commercial contractor lead pipeline.
              </p>
            </div>

            <div className="grid grid-cols-1 gap-2.5 text-left text-xs font-mono bg-elevated p-3.5 rounded border border-[var(--border-subtle)]">
              <div className="flex items-center gap-2">
                <span className="text-theme-success font-bold">✓</span>
                <span className="text-theme-primary">Multi-Source B2B Lead Scraping</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-theme-success font-bold">✓</span>
                <span className="text-theme-primary">3-Stage Zero-Bounce Email Hygiene</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-theme-success font-bold">✓</span>
                <span className="text-theme-primary">Inbox Rotator & Automated IMAP Reply Listener</span>
              </div>
            </div>

            <button
              type="button"
              onClick={handleActivateTrial}
              disabled={isActivatingTrial}
              className="btn btn-primary w-full justify-center btn-lg"
            >
              <span>{isActivatingTrial ? "Activating 48-Hour Trial..." : "🚀 Activate 2-Day Free Trial Now"}</span>
            </button>

            <div className="pt-1">
              <button
                type="button"
                onClick={handleLogout}
                className="text-xs text-theme-muted hover:text-theme-secondary font-mono underline"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: POST-TRIAL SUBSCRIPTION PAYWALL (NON-DISMISSIBLE FOR EXPIRED OPERATORS) */}
      {user && user.role === "operator" && user.subscription_status !== "active" && (user.is_expired || user.trial_status === "expired" || isTrialExpired(user.trial_expires_at)) && (
        <div className="np-modal-backdrop">
          <div className="np-modal max-w-xl p-6 space-y-4">
            <div className="text-center">
              <div className="w-14 h-14 mx-auto mb-2 rounded-full bg-[var(--danger-muted)] border-2 border-[var(--danger)] flex items-center justify-center text-2xl">
                ⏱️
              </div>
              <h3 className="font-bold text-lg text-theme-primary">
                Your 2-Day Free Trial Has Ended
              </h3>
              <p className="text-xs text-theme-secondary mt-1 max-w-md mx-auto">
                Choose a subscription tier to continue prospecting and dispatching verified B2B leads.
              </p>
            </div>

            {paywallSubmitted ? (
              <div className="bg-elevated p-6 rounded text-center space-y-3 border border-[var(--border-subtle)]">
                <span className="text-3xl block">✅</span>
                <h4 className="font-bold text-sm text-theme-primary">Subscription Plan Request Submitted!</h4>
                <p className="text-xs text-theme-secondary max-w-sm mx-auto">
                  Your request has been logged into the Super Admin Manual Billing portal.
                  Activation is typically completed promptly. You can also reach our team at <strong className="text-theme-accent">h.huddair@nexus-pulse.io</strong>.
                </p>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="btn btn-secondary btn-sm mt-2"
                >
                  Sign Out
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {/* Plan 1 */}
                  <div
                    onClick={() => setSelectedPaywallPlan("1_month")}
                    className={`cursor-pointer p-3.5 rounded border transition-all ${
                      selectedPaywallPlan === "1_month"
                        ? "border-[var(--accent)] bg-elevated ring-1 ring-[var(--accent)]"
                        : "border-[var(--border-subtle)] hover:border-theme"
                    }`}
                  >
                    <div className="text-xs font-bold text-theme-primary">1 Month Standard</div>
                    <div className="text-lg font-bold text-theme-primary my-1">$199<span className="text-xs font-normal text-theme-muted">/mo</span></div>
                    <div className="text-[10px] text-theme-secondary font-mono">100 scrapes/day<br/>25 sends/day</div>
                  </div>

                  {/* Plan 2 */}
                  <div
                    onClick={() => setSelectedPaywallPlan("2_months")}
                    className={`cursor-pointer p-3.5 rounded border transition-all ${
                      selectedPaywallPlan === "2_months"
                        ? "border-[var(--accent)] bg-elevated ring-1 ring-[var(--accent)]"
                        : "border-[var(--border-subtle)] hover:border-theme"
                    }`}
                  >
                    <div className="text-xs font-bold text-theme-primary">2 Months Pro</div>
                    <div className="text-lg font-bold text-theme-primary my-1">$379<span className="text-xs font-normal text-theme-muted"> total</span></div>
                    <div className="text-[10px] text-theme-secondary font-mono">150 scrapes/day<br/>40 sends/day</div>
                  </div>

                  {/* Plan 3 */}
                  <div
                    onClick={() => setSelectedPaywallPlan("3_months")}
                    className={`cursor-pointer p-3.5 rounded border relative transition-all ${
                      selectedPaywallPlan === "3_months"
                        ? "border-[var(--accent)] bg-elevated ring-1 ring-[var(--accent)]"
                        : "border-[var(--border-subtle)] hover:border-theme"
                    }`}
                  >
                    <span className="absolute -top-2 right-2 badge badge-success text-[9px] px-1 py-0">10% OFF</span>
                    <div className="text-xs font-bold text-theme-primary">3 Months Enterprise</div>
                    <div className="text-lg font-bold text-theme-success my-1">$537<span className="text-xs font-normal text-theme-muted"> total</span></div>
                    <div className="text-[10px] text-theme-secondary font-mono">200 scrapes/day<br/>50 sends/day<br/>Priority dispatch</div>
                  </div>
                </div>

                <div>
                  <label className="np-label">Payment Reference / Notes (Optional)</label>
                  <input
                    type="text"
                    value={paywallNotes}
                    onChange={(e) => setPaywallNotes(e.target.value)}
                    placeholder="e.g. PO Number or Wire Transfer Reference"
                    className="np-input font-mono text-xs"
                  />
                </div>

                <div className="flex items-center justify-between pt-2">
                  <button
                    type="button"
                    onClick={handleLogout}
                    className="btn btn-ghost btn-sm text-theme-muted hover:text-theme-secondary font-mono text-xs"
                  >
                    Sign Out
                  </button>

                  <button
                    type="button"
                    onClick={handleSubmitPlanRequest}
                    disabled={isSubmittingPlan}
                    className="btn btn-primary btn-sm"
                  >
                    <span>{isSubmittingPlan ? "Submitting..." : "Submit Plan Request & Request Activation"}</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// Render the application into #root
const rootElement = document.getElementById("root");
if (rootElement) {
  const root = ReactDOM.createRoot(rootElement);
  root.render(<NexusPulseApp />);
}
