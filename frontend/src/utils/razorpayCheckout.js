const SCRIPT_URL = 'https://checkout.razorpay.com/v1/checkout.js';

let scriptPromise = null;

export function loadRazorpayScript() {
  if (typeof window === 'undefined') {
    return Promise.reject(new Error('Razorpay is only available in the browser'));
  }
  if (window.Razorpay) {
    return Promise.resolve(window.Razorpay);
  }
  if (!scriptPromise) {
    scriptPromise = new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = SCRIPT_URL;
      script.async = true;
      script.onload = () => resolve(window.Razorpay);
      script.onerror = () => reject(new Error('Failed to load Razorpay checkout'));
      document.body.appendChild(script);
    });
  }
  return scriptPromise;
}

/**
 * Opens Razorpay checkout for doctor consultation.
 * @returns {Promise<object>} Razorpay payment response on success
 */
export async function openRazorpayCheckout({ order, user, doctor, onDismiss }) {
  const Razorpay = await loadRazorpayScript();
  const key = order.key_id || process.env.REACT_APP_RAZORPAY_KEY_ID;
  if (!key) {
    throw new Error('Razorpay key is not configured on the client');
  }

  return new Promise((resolve, reject) => {
    const options = {
      key,
      amount: (order.amount || 5) * 100,
      currency: order.currency || 'INR',
      name: 'Alpha-Cure',
      description: `Consultation with Dr. ${doctor.name}`,
      order_id: order.order_id,
      prefill: {
        name: user?.name || '',
        email: user?.email || '',
        contact: user?.phone || '',
      },
      theme: { color: '#0284c7' },
      handler: (response) => resolve(response),
      modal: {
        ondismiss: () => {
          onDismiss?.();
          reject(new Error('Payment cancelled'));
        },
      },
    };

    const rzp = new Razorpay(options);
    rzp.on('payment.failed', (response) => {
      reject(new Error(response.error?.description || 'Payment failed'));
    });
    rzp.open();
  });
}
