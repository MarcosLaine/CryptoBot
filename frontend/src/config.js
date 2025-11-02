// API configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://cryptobot-api-jcrn.onrender.com';

// Debug: verificar qual URL está sendo usada
console.log('🔗 API Base URL:', API_BASE_URL);
console.log('🔗 ENV Variable:', process.env.REACT_APP_API_URL);

export default API_BASE_URL;

