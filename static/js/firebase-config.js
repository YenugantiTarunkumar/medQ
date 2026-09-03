// MEDQ - Firebase Client SDK Initialization
const firebaseConfig = {
    apiKey: "AIzaSyA8u_kPdUFmJ5CzItynAkWuMjtHk1ntflg",
    authDomain: "medq-5346f.firebaseapp.com",
    databaseURL: "https://medq-5346f-default-rtdb.firebaseio.com",
    projectId: "medq-5346f",
    storageBucket: "medq-5346f.firebasestorage.app",
    messagingSenderId: "234560019157",
    appId: "1:234560019157:web:d9f7e528f1722721d6605c",
    measurementId: "G-JHVGR4GG0B"
};

// Initialize Firebase if compat libraries loaded
if (typeof firebase !== 'undefined') {
    if (!firebase.apps.length) {
        firebase.initializeApp(firebaseConfig);
        console.log("MedQ Firebase Connected:", firebaseConfig.projectId);
    }
}
