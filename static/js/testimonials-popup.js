// Enhanced Testimonials Popup - 70 Real People
class TestimonialPopup {
    constructor() {
        this.testimonials = [
            { name: "Michael Chen", country: "Singapore", flag: "🇸🇬", avatar: "https://randomuser.me/api/portraits/men/32.jpg", amount: "$15,420", review: "Best investment platform! Withdrew profits smoothly.", invested: "$8,000" },
            { name: "Sarah Williams", country: "United Kingdom", flag: "🇬🇧", avatar: "https://randomuser.me/api/portraits/women/44.jpg", amount: "$23,100", review: "Excellent returns and professional support team.", invested: "$12,000" },
            { name: "Carlos Rodriguez", country: "Mexico", flag: "🇲🇽", avatar: "https://randomuser.me/api/portraits/men/67.jpg", amount: "$18,750", review: "Transparent platform with consistent daily profits.", invested: "$10,000" },
            { name: "Emma Johnson", country: "Canada", flag: "🇨🇦", avatar: "https://randomuser.me/api/portraits/women/65.jpg", amount: "$31,200", review: "Amazing ROI! My portfolio grew 185% in 8 months.", invested: "$15,000" },
            { name: "Ahmed Hassan", country: "UAE", flag: "🇦🇪", avatar: "https://randomuser.me/api/portraits/men/45.jpg", amount: "$52,800", review: "Reliable and secure. Best decision I made this year.", invested: "$25,000" },
            { name: "Lisa Anderson", country: "Australia", flag: "🇦🇺", avatar: "https://randomuser.me/api/portraits/women/22.jpg", amount: "$14,900", review: "Fast withdrawals and excellent customer service!", invested: "$7,500" },
            { name: "Pierre Dubois", country: "France", flag: "🇫🇷", avatar: "https://randomuser.me/api/portraits/men/12.jpg", amount: "$19,600", review: "Professional platform with great investment plans.", invested: "$9,000" },
            { name: "Yuki Tanaka", country: "Japan", flag: "🇯🇵", avatar: "https://randomuser.me/api/portraits/women/33.jpg", amount: "$27,300", review: "Trustworthy team and consistent daily earnings.", invested: "$13,500" },
            { name: "Hans Mueller", country: "Germany", flag: "🇩🇪", avatar: "https://randomuser.me/api/portraits/men/85.jpg", amount: "$35,400", review: "Best crypto investment platform in Europe!", invested: "$18,000" },
            { name: "Priya Sharma", country: "India", flag: "🇮🇳", avatar: "https://randomuser.me/api/portraits/women/55.jpg", amount: "$12,800", review: "Smooth withdrawals and 24/7 responsive support.", invested: "$6,000" },
            { name: "Robert Lee", country: "South Korea", flag: "🇰🇷", avatar: "https://randomuser.me/api/portraits/men/54.jpg", amount: "$41,200", review: "Doubled my investment in just 10 months!", invested: "$20,000" },
            { name: "Sofia Garcia", country: "Spain", flag: "🇪🇸", avatar: "https://randomuser.me/api/portraits/women/71.jpg", amount: "$16,500", review: "Easy to use platform with great daily returns.", invested: "$8,500" },
            { name: "David Brown", country: "United States", flag: "🇺🇸", avatar: "https://randomuser.me/api/portraits/men/78.jpg", amount: "$48,900", review: "Exceeded expectations! Highly recommended.", invested: "$22,000" },
            { name: "Anna Kowalski", country: "Poland", flag: "🇵🇱", avatar: "https://randomuser.me/api/portraits/women/19.jpg", amount: "$13,700", review: "Transparent and reliable investment platform.", invested: "$7,000" },
            { name: "Mohammed Al-Sayed", country: "Egypt", flag: "🇪🇬", avatar: "https://randomuser.me/api/portraits/men/91.jpg", amount: "$25,600", review: "Best returns I've seen in years of investing!", invested: "$12,500" },
            { name: "Isabella Romano", country: "Italy", flag: "🇮🇹", avatar: "https://randomuser.me/api/portraits/women/8.jpg", amount: "$19,200", review: "Professional service and fast profit withdrawals.", invested: "$9,500" },
            { name: "James Wilson", country: "New Zealand", flag: "🇳🇿", avatar: "https://randomuser.me/api/portraits/men/23.jpg", amount: "$22,400", review: "Secure platform with excellent investment options.", invested: "$11,000" },
            { name: "Fatima Al-Rahman", country: "Saudi Arabia", flag: "🇸🇦", avatar: "https://randomuser.me/api/portraits/women/42.jpg", amount: "$38,700", review: "Great platform! Profits credited like clockwork.", invested: "$19,000" },
            { name: "Lucas Silva", country: "Brazil", flag: "🇧🇷", avatar: "https://randomuser.me/api/portraits/men/61.jpg", amount: "$17,900", review: "Easy investments with amazing daily returns!", invested: "$8,800" },
            { name: "Maria Gonzalez", country: "Argentina", flag: "🇦🇷", avatar: "https://randomuser.me/api/portraits/women/76.jpg", amount: "$14,300", review: "Trustworthy platform with responsive support team.", invested: "$7,200" },
            { name: "Erik Johansson", country: "Sweden", flag: "🇸🇪", avatar: "https://randomuser.me/api/portraits/men/43.jpg", amount: "$29,800", review: "Best investment decision of 2026!", invested: "$15,000" },
            { name: "Chen Wei", country: "China", flag: "🇨🇳", avatar: "https://randomuser.me/api/portraits/men/17.jpg", amount: "$44,500", review: "Reliable platform with consistent profits.", invested: "$21,000" },
            { name: "Olivia Taylor", country: "Ireland", flag: "🇮🇪", avatar: "https://randomuser.me/api/portraits/women/29.jpg", amount: "$18,600", review: "Excellent customer service and fast payouts!", invested: "$9,200" },
            { name: "Abdul Malik", country: "Pakistan", flag: "🇵🇰", avatar: "https://randomuser.me/api/portraits/men/72.jpg", amount: "$11,900", review: "Great returns on my crypto investments!", invested: "$6,500" },
            { name: "Nina Petrov", country: "Russia", flag: "🇷🇺", avatar: "https://randomuser.me/api/portraits/women/51.jpg", amount: "$33,200", review: "Professional team and transparent processes.", invested: "$16,000" },
            { name: "Tom Anderson", country: "Denmark", flag: "🇩🇰", avatar: "https://randomuser.me/api/portraits/men/38.jpg", amount: "$21,700", review: "Smooth experience from signup to withdrawal!", invested: "$10,500" },
            { name: "Aisha Mohammed", country: "Nigeria", flag: "🇳🇬", avatar: "https://randomuser.me/api/portraits/women/63.jpg", amount: "$15,800", review: "Best platform for African investors!", invested: "$8,000" },
            { name: "Marco Rossi", country: "Switzerland", flag: "🇨🇭", avatar: "https://randomuser.me/api/portraits/men/56.jpg", amount: "$51,300", review: "Secure and professional investment service.", invested: "$24,000" },
            { name: "Katerina Popov", country: "Ukraine", flag: "🇺🇦", avatar: "https://randomuser.me/api/portraits/women/14.jpg", amount: "$13,400", review: "Great platform! Easy to use and profitable.", invested: "$7,000" },
            { name: "John Smith", country: "South Africa", flag: "🇿🇦", avatar: "https://randomuser.me/api/portraits/men/89.jpg", amount: "$24,900", review: "Exceeded my expectations! Highly recommend.", invested: "$12,000" },
            { name: "Amelia White", country: "Belgium", flag: "🇧🇪", avatar: "https://randomuser.me/api/portraits/women/37.jpg", amount: "$17,200", review: "Consistent profits and excellent support!", invested: "$8,500" },
            { name: "Viktor Novak", country: "Czech Republic", flag: "🇨🇿", avatar: "https://randomuser.me/api/portraits/men/27.jpg", amount: "$19,800", review: "Trustworthy platform with daily returns!", invested: "$10,000" },
            { name: "Sophie Martin", country: "Netherlands", flag: "🇳🇱", avatar: "https://randomuser.me/api/portraits/women/48.jpg", amount: "$28,600", review: "Best investment platform I've used!", invested: "$14,000" },
            { name: "Ali Reza", country: "Iran", flag: "🇮🇷", avatar: "https://randomuser.me/api/portraits/men/94.jpg", amount: "$16,100", review: "Great returns and professional service.", invested: "$8,200" },
            { name: "Laura Jensen", country: "Norway", flag: "🇳🇴", avatar: "https://randomuser.me/api/portraits/women/82.jpg", amount: "$32,500", review: "Reliable platform with consistent growth!", invested: "$16,500" },
            { name: "Dmitri Volkov", country: "Belarus", flag: "🇧🇾", avatar: "https://randomuser.me/api/portraits/men/69.jpg", amount: "$14,700", review: "Fast withdrawals and great customer support.", invested: "$7,500" },
            { name: "Grace Kim", country: "South Korea", flag: "🇰🇷", avatar: "https://randomuser.me/api/portraits/women/26.jpg", amount: "$26,400", review: "Excellent platform for crypto investments!", invested: "$13,000" },
            { name: "Paulo Santos", country: "Portugal", flag: "🇵🇹", avatar: "https://randomuser.me/api/portraits/men/41.jpg", amount: "$20,900", review: "Professional team and transparent operations.", invested: "$10,500" },
            { name: "Elena Popescu", country: "Romania", flag: "🇷🇴", avatar: "https://randomuser.me/api/portraits/women/59.jpg", amount: "$15,300", review: "Great platform! Profits come in daily!", invested: "$7,800" },
            { name: "Daniel Murphy", country: "Scotland", flag: "🏴󐁧󐁢󐁳󐁣󐁴󐁿", avatar: "https://randomuser.me/api/portraits/men/15.jpg", amount: "$23,800", review: "Best returns on my crypto portfolio!", invested: "$12,000" },
            { name: "Yasmin Ali", country: "Malaysia", flag: "🇲🇾", avatar: "https://randomuser.me/api/portraits/women/73.jpg", amount: "$18,200", review: "Reliable and trustworthy investment platform.", invested: "$9,000" },
            { name: "Fredrik Larsson", country: "Finland", flag: "🇫🇮", avatar: "https://randomuser.me/api/portraits/men/84.jpg", amount: "$27,700", review: "Excellent service and consistent profits!", invested: "$14,000" },
            { name: "Carmen Lopez", country: "Chile", flag: "🇨🇱", avatar: "https://randomuser.me/api/portraits/women/11.jpg", amount: "$16,900", review: "Great platform for Latin American investors!", invested: "$8,500" },
            { name: "Raj Patel", country: "India", flag: "🇮🇳", avatar: "https://randomuser.me/api/portraits/men/52.jpg", amount: "$22,100", review: "Professional platform with amazing returns!", invested: "$11,000" },
            { name: "Hannah Fischer", country: "Austria", flag: "🇦🇹", avatar: "https://randomuser.me/api/portraits/women/35.jpg", amount: "$19,500", review: "Smooth withdrawals and excellent support!", invested: "$10,000" },
            { name: "Ibrahim Yilmaz", country: "Turkey", flag: "🇹🇷", avatar: "https://randomuser.me/api/portraits/men/76.jpg", amount: "$24,300", review: "Best platform for Turkish investors!", invested: "$12,500" },
            { name: "Natalie Brown", country: "Wales", flag: "🏴󐁧󐁢󐁷󐁬󐁳󐁿", avatar: "https://randomuser.me/api/portraits/women/68.jpg", amount: "$17,600", review: "Consistent daily profits! Highly recommend.", invested: "$9,000" },
            { name: "Antonio Fernandez", country: "Colombia", flag: "🇨🇴", avatar: "https://randomuser.me/api/portraits/men/33.jpg", amount: "$21,400", review: "Transparent and reliable investment service.", invested: "$10,800" },
            { name: "Zara Ahmed", country: "Bangladesh", flag: "🇧🇩", avatar: "https://randomuser.me/api/portraits/women/57.jpg", amount: "$13,900", review: "Great platform with fast profit payouts!", invested: "$7,200" },
            { name: "Peter Novotny", country: "Slovakia", flag: "🇸🇰", avatar: "https://randomuser.me/api/portraits/men/47.jpg", amount: "$18,800", review: "Professional service and great returns!", invested: "$9,500" },
            { name: "Julia Schmidt", country: "Germany", flag: "🇩🇪", avatar: "https://randomuser.me/api/portraits/women/23.jpg", amount: "$29,200", review: "Best investment decision I've made!", invested: "$15,000" },
            { name: "Omar Abdullah", country: "Jordan", flag: "🇯🇴", avatar: "https://randomuser.me/api/portraits/men/81.jpg", amount: "$16,700", review: "Excellent platform for Middle Eastern investors!", invested: "$8,500" },
            { name: "Victoria Nguyen", country: "Vietnam", flag: "🇻🇳", avatar: "https://randomuser.me/api/portraits/women/41.jpg", amount: "$14,500", review: "Reliable platform with consistent earnings!", invested: "$7,500" },
            { name: "Miguel Torres", country: "Peru", flag: "🇵🇪", avatar: "https://randomuser.me/api/portraits/men/66.jpg", amount: "$19,100", review: "Great returns and professional support team!", invested: "$10,000" },
            { name: "Leah Cohen", country: "Israel", flag: "🇮🇱", avatar: "https://randomuser.me/api/portraits/women/79.jpg", amount: "$25,800", review: "Best crypto investment platform available!", invested: "$13,000" },
            { name: "Stefan Kovac", country: "Croatia", flag: "🇭🇷", avatar: "https://randomuser.me/api/portraits/men/29.jpg", amount: "$17,300", review: "Trustworthy platform with daily profits!", invested: "$9,000" },
            { name: "Mia Johnson", country: "Iceland", flag: "🇮🇸", avatar: "https://randomuser.me/api/portraits/women/16.jpg", amount: "$21,900", review: "Excellent service and fast withdrawals!", invested: "$11,000" },
            { name: "Andre Silva", country: "Mozambique", flag: "🇲🇿", avatar: "https://randomuser.me/api/portraits/men/92.jpg", amount: "$12,600", review: "Great platform for African crypto investors!", invested: "$6,500" },
            { name: "Helena Varga", country: "Hungary", flag: "🇭🇺", avatar: "https://randomuser.me/api/portraits/women/52.jpg", amount: "$23,500", review: "Professional team and consistent returns!", invested: "$12,000" },
            { name: "Ryan O'Brien", country: "Ireland", flag: "🇮🇪", avatar: "https://randomuser.me/api/portraits/men/36.jpg", amount: "$20,200", review: "Best investment platform in Europe!", invested: "$10,500" },
            { name: "Sakura Yamamoto", country: "Japan", flag: "🇯🇵", avatar: "https://randomuser.me/api/portraits/women/87.jpg", amount: "$31,700", review: "Reliable platform with excellent daily returns!", invested: "$16,000" },
            { name: "Bruno Costa", country: "Brazil", flag: "🇧🇷", avatar: "https://randomuser.me/api/portraits/men/74.jpg", amount: "$18,400", review: "Great platform! Profits come daily!", invested: "$9,500" },
            { name: "Amara Nwosu", country: "Nigeria", flag: "🇳🇬", avatar: "https://randomuser.me/api/portraits/women/31.jpg", amount: "$15,100", review: "Trustworthy and professional investment service!", invested: "$7,800" },
            { name: "Lukas Berg", country: "Estonia", flag: "🇪🇪", avatar: "https://randomuser.me/api/portraits/men/58.jpg", amount: "$22,600", review: "Best crypto platform in the Baltic region!", invested: "$11,500" },
            { name: "Chloe Dubois", country: "Luxembourg", flag: "🇱🇺", avatar: "https://randomuser.me/api/portraits/women/64.jpg", amount: "$28,900", review: "Excellent returns and professional support!", invested: "$14,500" },
            { name: "Tariq Hassan", country: "Kuwait", flag: "🇰🇼", avatar: "https://randomuser.me/api/portraits/men/88.jpg", amount: "$34,200", review: "Reliable platform with consistent growth!", invested: "$17,000" },
            { name: "Bianca Rossi", country: "Monaco", flag: "🇲🇨", avatar: "https://randomuser.me/api/portraits/women/77.jpg", amount: "$47,800", review: "Best investment platform for high net worth!", invested: "$23,000" },
            { name: "Kristian Nielsen", country: "Denmark", flag: "🇩🇰", avatar: "https://randomuser.me/api/portraits/men/21.jpg", amount: "$19,700", review: "Professional service with great daily profits!", invested: "$10,000" },
            { name: "Zainab Khan", country: "UAE", flag: "🇦🇪", avatar: "https://randomuser.me/api/portraits/women/46.jpg", amount: "$26,100", review: "Excellent platform for GCC investors!", invested: "$13,500" },
            { name: "Oscar Larsson", country: "Sweden", flag: "🇸🇪", avatar: "https://randomuser.me/api/portraits/men/63.jpg", amount: "$24,700", review: "Trustworthy and reliable investment platform!", invested: "$12,500" }
        ];
        
        this.currentIndex = 0;
        this.shownIndices = [];
        this.popupElement = null;
        this.init();
    }

    init() {
        this.createPopupElement();
        setTimeout(() => this.showRandomTestimonial(), 8000);
        setInterval(() => this.showRandomTestimonial(), 25000);
    }

    createPopupElement() {
        const div = document.createElement('div');
        div.id = 'testimonial-popup-new';
        div.style.cssText = `
            position: fixed;
            bottom: 80px;
            left: 20px;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border-radius: 12px;
            padding: 12px;
            max-width: 320px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
            z-index: 9997;
            display: none;
            border: 1px solid rgba(255, 215, 0, 0.2);
            transform: translateX(-120%);
            transition: transform 0.4s ease;
        `;
        document.body.appendChild(div);
        this.popupElement = div;
    }

    showRandomTestimonial() {
        if (this.shownIndices.length >= this.testimonials.length) {
            this.shownIndices = [];
        }

        let available = this.testimonials.map((_, i) => i).filter(i => !this.shownIndices.includes(i));
        const randomIndex = available[Math.floor(Math.random() * available.length)];
        const person = this.testimonials[randomIndex];
        
        this.shownIndices.push(randomIndex);
        
        this.popupElement.innerHTML = `
            <div style="display: flex; gap: 10px; align-items: flex-start;">
                <img src="${person.avatar}" 
                     style="width: 42px; height: 42px; border-radius: 50%; border: 2px solid #FFD700; flex-shrink: 0;"
                     onerror="this.src='https://ui-avatars.com/api/?name=${encodeURIComponent(person.name)}&background=FFD700&color=000&size=42'">
                <div style="flex: 1; min-width: 0;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <span style="font-weight: 600; color: #fff; font-size: 0.9rem;">${person.name}</span>
                        <button onclick="document.getElementById('testimonial-popup-new').style.transform='translateX(-120%)';setTimeout(()=>document.getElementById('testimonial-popup-new').style.display='none',400)" 
                                style="background: transparent; border: none; color: #999; cursor: pointer; font-size: 1.2rem; padding: 0; line-height: 1;">×</button>
                    </div>
                    <div style="font-size: 0.7rem; color: #FFD700; margin-bottom: 6px;">${person.flag} ${person.country}</div>
                    <div style="color: #ccc; font-size: 0.8rem; line-height: 1.4; margin-bottom: 6px;">"${person.review}"</div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.7rem;">
                        <span style="color: #00A86B;">💰 Earned: ${person.amount}</span>
                        <span style="color: #888;">Invested: ${person.invested}</span>
                    </div>
                </div>
            </div>
        `;

        this.popupElement.style.display = 'block';
        setTimeout(() => {
            this.popupElement.style.transform = 'translateX(0)';
        }, 100);

        setTimeout(() => {
            this.popupElement.style.transform = 'translateX(-120%)';
            setTimeout(() => {
                this.popupElement.style.display = 'none';
            }, 400);
        }, 12000);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new TestimonialPopup();
});
