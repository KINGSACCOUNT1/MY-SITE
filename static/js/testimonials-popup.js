/**
 * Testimonials Popup System
 * Shows random user reviews/testimonials at intervals
 */

const testimonials = [
    {
        name: "Michael Thompson",
        country: "United Kingdom",
        amount: "$15,000",
        action: "withdrew",
        rating: 5,
        message: "Excellent service! Fast and reliable withdrawals.",
        avatar: "avatar-1.jpg"
    },
    {
        name: "Sarah Williams",
        country: "United States",
        amount: "$8,500",
        action: "earned",
        rating: 5,
        message: "Amazing returns! Best investment platform I've used.",
        avatar: "avatar-2.jpg"
    },
    {
        name: "David Chen",
        country: "Singapore",
        amount: "$12,300",
        action: "withdrew",
        rating: 5,
        message: "Professional team and transparent processes.",
        avatar: "avatar-3.jpg"
    },
    {
        name: "Emma Rodriguez",
        country: "Spain",
        amount: "$6,750",
        action: "earned",
        rating: 5,
        message: "Great platform for passive income!",
        avatar: "avatar-4.jpg"
    },
    {
        name: "James Anderson",
        country: "Canada",
        amount: "$20,000",
        action: "withdrew",
        rating: 5,
        message: "Trustworthy platform with consistent returns.",
        avatar: "avatar-5.jpg"
    },
    {
        name: "Sophie Martin",
        country: "France",
        amount: "$9,200",
        action: "earned",
        rating: 5,
        message: "Very impressed with the ROI and customer support.",
        avatar: "avatar-6.jpg"
    },
    {
        name: "Mohammed Al-Rashid",
        country: "UAE",
        amount: "$25,000",
        action: "withdrew",
        rating: 5,
        message: "Secure and efficient investment platform."
    },
    {
        name: "Lisa Johnson",
        country: "Australia",
        amount: "$11,500",
        action: "earned",
        rating: 5,
        message: "Highly recommend! Consistent profits every day."
    },
    {
        name: "Carlos Silva",
        country: "Brazil",
        amount: "$7,800",
        action: "withdrew",
        rating: 5,
        message: "Fast withdrawals and excellent customer service."
    },
    {
        name: "Anna Kowalski",
        country: "Poland",
        amount: "$13,600",
        action: "earned",
        rating: 5,
        message: "Best investment decision I've made this year!"
    },
    {
        name: "Robert Lee",
        country: "South Korea",
        amount: "$18,900",
        action: "withdrew",
        rating: 5,
        message: "Professional platform with great returns."
    },
    {
        name: "Maria Garcia",
        country: "Mexico",
        amount: "$5,400",
        action: "earned",
        rating: 5,
        message: "Easy to use and very profitable!"
    },
    {
        name: "Thomas Müller",
        country: "Germany",
        amount: "$22,000",
        action: "withdrew",
        rating: 5,
        message: "Reliable and transparent investment platform."
    },
    {
        name: "Olivia Brown",
        country: "New Zealand",
        amount: "$8,900",
        action: "earned",
        rating: 5,
        message: "Fantastic ROI! Exceeded my expectations."
    },
    {
        name: "Ahmed Hassan",
        country: "Egypt",
        amount: "$10,200",
        action: "withdrew",
        rating: 5,
        message: "Great platform for long-term investments."
    },
    {
        name: "Isabella Rossi",
        country: "Italy",
        amount: "$14,700",
        action: "earned",
        rating: 5,
        message: "Outstanding service and impressive returns!"
    },
    {
        name: "William Taylor",
        country: "Ireland",
        amount: "$16,500",
        action: "withdrew",
        rating: 5,
        message: "Secure platform with fast processing times."
    },
    {
        name: "Yuki Tanaka",
        country: "Japan",
        amount: "$19,300",
        action: "earned",
        rating: 5,
        message: "Professional team and excellent investment options."
    },
    {
        name: "Lucas Andersen",
        country: "Norway",
        amount: "$12,800",
        action: "withdrew",
        rating: 5,
        message: "Very satisfied with the returns and service."
    },
    {
        name: "Priya Sharma",
        country: "India",
        amount: "$7,200",
        action: "earned",
        rating: 5,
        message: "Great platform for beginners and experts alike!"
    }
];

class TestimonialPopup {
    constructor() {
        this.container = null;
        this.shownIndices = new Set();
        this.visiblePopups = 0;
        this.maxVisiblePopups = 3;
        this.init();
    }

    init() {
        // Create popup container
        this.createContainer();
        
        // Load confetti animation CSS if needed
        this.loadConfettiStyles();
        
        // Start showing testimonials after 10 seconds
        setTimeout(() => {
            this.showRandomTestimonial();
            // Show a new one every 15-20 seconds
            setInterval(() => {
                if (this.visiblePopups < this.maxVisiblePopups) {
                    this.showRandomTestimonial();
                }
            }, this.getRandomInterval(15000, 20000));
        }, 10000);
    }

    createContainer() {
        // Check if container already exists
        if (document.getElementById('testimonial-popup-container')) {
            return;
        }

        const container = document.createElement('div');
        container.id = 'testimonial-popup-container';
        container.style.cssText = `
            position: fixed;
            bottom: 80px;
            left: 20px;
            z-index: 9997;
            font-family: 'Inter', sans-serif;
            display: flex;
            flex-direction: column;
            gap: 15px;
            max-width: 350px;
        `;
        document.body.appendChild(container);
        this.container = container;
    }
    
    loadConfettiStyles() {
        if (document.getElementById('confetti-styles')) {
            return;
        }
        
        const style = document.createElement('style');
        style.id = 'confetti-styles';
        style.textContent = `
            @keyframes confetti-fall {
                0% {
                    transform: translateY(-100vh) translateX(0) rotate(0deg);
                    opacity: 1;
                }
                100% {
                    transform: translateY(100vh) translateX(100px) rotate(720deg);
                    opacity: 0;
                }
            }
            
            @keyframes slideInUp {
                from {
                    transform: translateY(30px);
                    opacity: 0;
                }
                to {
                    transform: translateY(0);
                    opacity: 1;
                }
            }
            
            .confetti {
                position: fixed;
                width: 10px;
                height: 10px;
                pointer-events: none;
                z-index: 9999;
                animation: confetti-fall 2s forwards;
            }
            
            .testimonial-popup {
                animation: slideInUp 0.4s ease forwards !important;
            }
        `;
        document.head.appendChild(style);
    }

    getRandomInterval(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }

    getRandomTestimonial() {
        // Reset if all testimonials have been shown
        if (this.shownIndices.size >= testimonials.length) {
            this.shownIndices.clear();
        }

        let randomIndex;
        do {
            randomIndex = Math.floor(Math.random() * testimonials.length);
        } while (this.shownIndices.has(randomIndex));

        this.shownIndices.add(randomIndex);
        return testimonials[randomIndex];
    }

    showRandomTestimonial() {
        if (this.visiblePopups >= this.maxVisiblePopups) {
            return;
        }
        
        const testimonial = this.getRandomTestimonial();
        const popup = this.createPopupElement(testimonial);
        
        this.container.appendChild(popup);
        this.visiblePopups++;

        // Animate in with slide-in from bottom-right
        setTimeout(() => {
            popup.style.transform = 'translateY(0)';
            popup.style.opacity = '1';
        }, 10);

        // Auto-hide after 8 seconds
        setTimeout(() => {
            this.hidePopup(popup);
        }, 8000);
    }

    createPopupElement(testimonial) {
        const popup = document.createElement('div');
        popup.className = 'testimonial-popup';
        popup.style.cssText = `
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 18px 22px;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            min-width: 280px;
            max-width: 280px;
            transform: translateY(30px);
            opacity: 0;
            transition: all 0.4s ease;
            cursor: pointer;
            position: relative;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.1);
        `;

        // Add shimmer effect
        const shimmer = document.createElement('div');
        shimmer.style.cssText = `
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            animation: shimmer 2s infinite;
        `;
        popup.appendChild(shimmer);

        // Add CSS animation for shimmer
        if (!document.getElementById('testimonial-animations')) {
            const style = document.createElement('style');
            style.id = 'testimonial-animations';
            style.textContent = `
                @keyframes shimmer {
                    0% { left: -100%; }
                    100% { left: 100%; }
                }
                .testimonial-popup:hover {
                    transform: translateY(0) scale(1.02);
                    box-shadow: 0 15px 40px rgba(0, 0, 0, 0.4);
                }
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.7; }
                }
                .new-badge {
                    animation: pulse 1s ease-in-out infinite;
                }
            `;
            document.head.appendChild(style);
        }

        const content = document.createElement('div');
        content.style.position = 'relative';
        content.style.zIndex = '1';
        // Header with icon
        const header = document.createElement('div');
        header.style.cssText = `
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
            gap: 12px;
        `;

        // Add avatar
        const avatarImg = document.createElement('img');
        avatarImg.src = `/static/images/avatars/${testimonial.avatar || 'avatar-1.jpg'}`;
        avatarImg.alt = testimonial.name;
        avatarImg.style.cssText = `
            width: 50px;
            height: 50px;
            border-radius: 50%;
            object-fit: cover;
            border: 2px solid rgba(255,255,255,0.3);
        `;

        const iconText = document.createElement('div');
        iconText.style.cssText = `
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 600;
        `;
        
        const icon = testimonial.action === 'withdrew' ? '💰' : '🎉';
        iconText.innerHTML = `<span style="font-size: 20px;">${icon}</span> 
                              <span style="font-size: 14px;">New ${testimonial.action === 'withdrew' ? 'Withdrawal' : 'Profit'}</span>`;

        const closeBtn = document.createElement('button');
        closeBtn.innerHTML = '×';
        closeBtn.style.cssText = `
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            font-size: 20px;
            cursor: pointer;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 0;
            line-height: 1;
        `;
        closeBtn.onclick = (e) => {
            e.stopPropagation();
            this.hidePopup(popup);
        };

        header.appendChild(avatarImg);
        header.appendChild(iconText);
        header.appendChild(closeBtn);

        // Main content
        const mainContent = document.createElement('div');
        mainContent.innerHTML = `
            <div style="font-weight: 700; font-size: 16px; margin-bottom: 4px;">
                ${testimonial.name}
            </div>
            <div style="font-size: 12px; opacity: 0.9; margin-bottom: 8px;">
                <span style="opacity: 0.8;">📍</span> ${testimonial.country}
            </div>
            <div style="background: rgba(255,255,255,0.15); padding: 8px 12px; border-radius: 8px; margin-bottom: 8px;">
                <div style="font-size: 20px; font-weight: 700; color: #ffd700;">
                    ${testimonial.amount}
                </div>
                <div style="font-size: 11px; opacity: 0.9;">
                    ${testimonial.action === 'withdrew' ? 'Successfully withdrawn' : 'Profit earned'}
                </div>
            </div>
            <div style="font-size: 11px; opacity: 0.95; font-style: italic;">
                "${testimonial.message}"
            </div>
            <div style="margin-top: 6px;">
                ${'⭐'.repeat(testimonial.rating)}
            </div>
        `;

        content.appendChild(header);
        content.appendChild(mainContent);
        popup.appendChild(content);

        return popup;
    }

    hidePopup(popup) {
        popup.style.transform = 'translateY(30px)';
        popup.style.opacity = '0';
        this.visiblePopups--;
        
        setTimeout(() => {
            if (popup.parentNode) {
                popup.parentNode.removeChild(popup);
            }
        }, 400);
    }
    
    showConfetti() {
        const confettiCount = 20;
        const colors = ['#FFD700', '#00A86B', '#667eea', '#764ba2', '#FF6B6B'];
        
        for (let i = 0; i < confettiCount; i++) {
            const confetti = document.createElement('div');
            confetti.className = 'confetti';
            confetti.style.left = Math.random() * window.innerWidth + 'px';
            confetti.style.top = '-10px';
            confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
            confetti.style.borderRadius = Math.random() > 0.5 ? '50%' : '0%';
            confetti.style.animation = `confetti-fall ${1.5 + Math.random() * 1}s forwards`;
            document.body.appendChild(confetti);
            
            setTimeout(() => confetti.remove(), 2500);
        }
    }
}

// Initialize testimonial popup when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new TestimonialPopup();
    });
} else {
    new TestimonialPopup();
}
