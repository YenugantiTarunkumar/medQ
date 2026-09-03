const translations = {
    en: {
        appName: "MedQ",
        navDashboard: "Dashboard",
        navHospitals: "Find Hospitals",
        navAppointments: "Appointments",
        navQueue: "Live Queue",
        navTriage: "AI Triage",
        navAssistant: "Health Assistant",
        navEmergency: "Emergency",
        navBeds: "Beds & Rooms",
        navInventory: "Inventory",
        navAnalytics: "Analytics",
        navUsers: "Users",
        logout: "Logout",
        login: "Login",
        welcome: "Welcome to MedQ Healthcare",
        searchPlaceholder: "Search hospitals, doctors, medicines..."
    },
    te: {
        appName: "మెడ్‌క్యూ",
        navDashboard: "డాష్‌బోర్డ్",
        navHospitals: "ఆసుపత్రులను కనుగొనండి",
        navAppointments: "అపాయింట్‌మెంట్‌లు",
        navQueue: "లైవ్ క్యూ",
        navTriage: "AI ట్రయాజ్",
        navAssistant: "ఆరోగ్య సహాయకుడు",
        navEmergency: "అత్యవసర చికిత్స",
        navBeds: "బెడ్స్ & రూమ్‌లు",
        navInventory: "ఇన్వెంటరీ",
        navAnalytics: "విశ్లేషణలు",
        navUsers: "వినియోగదారులు",
        logout: "లాగ్ అవుట్",
        login: "లాగిన్",
        welcome: "మెడ్‌క్యూ హెల్త్‌కేర్‌కు స్వాగతం",
        searchPlaceholder: "ఆసుపత్రులు, వైద్యులను శోధించండి..."
    },
    ta: {
        appName: "மெட்கியூ",
        navDashboard: "டாஷ்போர்டு",
        navHospitals: "மருத்துவமனைகளைக் கண்டறியவும்",
        navAppointments: "அப்பாயிண்ட்மெண்டுகள்",
        navQueue: "நேரடி வரிசை",
        navTriage: "AI டிரியேஜ்",
        navAssistant: "சுகாதார உதவியாளர்",
        navEmergency: "அவசர சிகிச்சை",
        navBeds: "படுக்கைகள் மற்றும் அறைகள்",
        navInventory: "சரக்கு",
        navAnalytics: "பகுப்பாய்வு",
        navUsers: "பயனர்கள்",
        logout: "வெளியேறு",
        login: "உள்நுழைய",
        welcome: "மெட்கியூ ஹெல்த்கேருக்கு வரவேற்கிறோம்",
        searchPlaceholder: "மருத்துவமனைகளைத் தேடுங்கள்..."
    },
    hi: {
        appName: "मेडक्यू",
        navDashboard: "डैशबोर्ड",
        navHospitals: "अस्पताल खोजें",
        navAppointments: "अपॉइंटमेंट",
        navQueue: "लाइव कतार",
        navTriage: "एआई ट्राइएज",
        navAssistant: "स्वास्थ्य सहायक",
        navEmergency: "आपातकालीन सेवा",
        navBeds: "बेड और कमरे",
        navInventory: "इन्वेंटरी",
        navAnalytics: "विश्लेषण",
        navUsers: "उपयोगकर्ता",
        logout: "लॉग आउट",
        login: "लॉग इन",
        welcome: "मेडक्यू में आपका स्वागत है",
        searchPlaceholder: "अस्पताल, डॉक्टर खोजें..."
    }
};

function changeLanguage(langCode) {
    localStorage.setItem('medq_lang', langCode);
    const langObj = translations[langCode] || translations['en'];
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (langObj[key]) {
            el.innerText = langObj[key];
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const savedLang = localStorage.getItem('medq_lang') || 'en';
    const langSelect = document.getElementById('langSelect');
    if (langSelect) {
        langSelect.value = savedLang;
        langSelect.addEventListener('change', (e) => changeLanguage(e.target.value));
    }
    changeLanguage(savedLang);
});
