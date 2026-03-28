"""
Receipt Generator for Elite Wealth Capital
Generates PDF receipts for deposits, withdrawals, and investments
"""
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch, mm
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from django.conf import settings
import os


class ReceiptGenerator:
    """Generate professional PDF receipts for transactions"""
    
    # Brand colors
    GOLD = HexColor('#FFD700')
    DARK_BLUE = HexColor('#0A1F44')
    LIGHT_BLUE = HexColor('#1e3a8a')
    WHITE = HexColor('#ffffff')
    GRAY = HexColor('#94a3b8')
    GREEN = HexColor('#00A86B')
    RED = HexColor('#EF4444')
    
    def __init__(self):
        self.width, self.height = A4
        self.styles = getSampleStyleSheet()
    
    def _draw_header(self, c, receipt_type):
        """Draw the receipt header with logo and company info"""
        # Background header bar
        c.setFillColor(self.DARK_BLUE)
        c.rect(0, self.height - 120, self.width, 120, fill=True, stroke=False)
        
        # Company name
        c.setFillColor(self.GOLD)
        c.setFont("Helvetica-Bold", 24)
        c.drawString(40, self.height - 50, "ELITE WEALTH CAPITAL")
        
        # Tagline
        c.setFillColor(self.WHITE)
        c.setFont("Helvetica", 10)
        c.drawString(40, self.height - 70, "Premium Investment Solutions")
        
        # Receipt type badge
        c.setFillColor(self.GOLD)
        c.roundRect(self.width - 180, self.height - 70, 140, 35, 5, fill=True, stroke=False)
        c.setFillColor(self.DARK_BLUE)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(self.width - 110, self.height - 52, f"{receipt_type.upper()} RECEIPT")
        
        # Website
        c.setFillColor(self.GRAY)
        c.setFont("Helvetica", 9)
        c.drawString(40, self.height - 100, "www.elitewealthcapita.uk")
        
    def _draw_receipt_info(self, c, receipt_id, date, status):
        """Draw receipt ID, date, and status"""
        y_pos = self.height - 160
        
        # Receipt ID box
        c.setFillColor(HexColor('#f8fafc'))
        c.roundRect(30, y_pos - 60, self.width - 60, 70, 8, fill=True, stroke=False)
        
        # Receipt ID
        c.setFillColor(self.DARK_BLUE)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y_pos - 15, "Receipt ID:")
        c.setFont("Helvetica", 11)
        c.drawString(130, y_pos - 15, str(receipt_id))
        
        # Date
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y_pos - 35, "Date:")
        c.setFont("Helvetica", 11)
        c.drawString(130, y_pos - 35, date.strftime("%B %d, %Y at %I:%M %p"))
        
        # Status
        c.setFont("Helvetica-Bold", 11)
        c.drawString(350, y_pos - 15, "Status:")
        
        # Status badge
        status_colors = {
            'completed': self.GREEN,
            'confirmed': self.GREEN,
            'approved': self.GREEN,
            'pending': HexColor('#FFD700'),
            'processing': HexColor('#3B82F6'),
            'rejected': self.RED,
            'failed': self.RED,
        }
        status_color = status_colors.get(status.lower(), self.GRAY)
        
        c.setFillColor(status_color)
        c.roundRect(410, y_pos - 25, 80, 20, 3, fill=True, stroke=False)
        c.setFillColor(self.WHITE)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(450, y_pos - 19, status.upper())
        
        return y_pos - 80
    
    def _draw_user_info(self, c, y_pos, user):
        """Draw user information section"""
        c.setFillColor(self.DARK_BLUE)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y_pos, "ACCOUNT HOLDER")
        
        c.setStrokeColor(self.GOLD)
        c.setLineWidth(2)
        c.line(40, y_pos - 5, 180, y_pos - 5)
        
        y_pos -= 25
        c.setFont("Helvetica", 10)
        c.setFillColor(HexColor('#374151'))
        
        c.drawString(40, y_pos, f"Name: {user.full_name}")
        y_pos -= 18
        c.drawString(40, y_pos, f"Email: {user.email}")
        y_pos -= 18
        if hasattr(user, 'account_id') and user.account_id:
            c.drawString(40, y_pos, f"Account ID: {user.account_id}")
            y_pos -= 18
        
        return y_pos - 20
    
    def _draw_transaction_details(self, c, y_pos, details):
        """Draw transaction details table"""
        c.setFillColor(self.DARK_BLUE)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y_pos, "TRANSACTION DETAILS")
        
        c.setStrokeColor(self.GOLD)
        c.setLineWidth(2)
        c.line(40, y_pos - 5, 200, y_pos - 5)
        
        y_pos -= 30
        
        # Table header
        c.setFillColor(self.LIGHT_BLUE)
        c.roundRect(30, y_pos - 5, self.width - 60, 25, 3, fill=True, stroke=False)
        
        c.setFillColor(self.WHITE)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y_pos + 3, "Description")
        c.drawRightString(self.width - 50, y_pos + 3, "Value")
        
        y_pos -= 30
        
        # Table rows
        c.setFillColor(HexColor('#374151'))
        c.setFont("Helvetica", 10)
        
        row_bg = True
        for key, value in details.items():
            if row_bg:
                c.setFillColor(HexColor('#f8fafc'))
                c.rect(30, y_pos - 5, self.width - 60, 22, fill=True, stroke=False)
            
            c.setFillColor(HexColor('#374151'))
            c.drawString(50, y_pos + 3, key)
            
            # Highlight amount
            if 'amount' in key.lower():
                c.setFillColor(self.GREEN)
                c.setFont("Helvetica-Bold", 11)
            
            c.drawRightString(self.width - 50, y_pos + 3, str(value))
            c.setFont("Helvetica", 10)
            
            y_pos -= 22
            row_bg = not row_bg
        
        return y_pos - 20
    
    def _draw_footer(self, c):
        """Draw receipt footer"""
        # Footer line
        c.setStrokeColor(self.GRAY)
        c.setLineWidth(0.5)
        c.line(40, 100, self.width - 40, 100)
        
        # Footer text
        c.setFillColor(self.GRAY)
        c.setFont("Helvetica", 8)
        c.drawCentredString(self.width / 2, 80, "This is an automatically generated receipt. Please keep it for your records.")
        c.drawCentredString(self.width / 2, 65, "For any queries, contact support@elitewealthcapita.uk")
        c.drawCentredString(self.width / 2, 50, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # Company info
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(self.width / 2, 30, "Elite Wealth Capital | www.elitewealthcapita.uk")
    
    def generate_deposit_receipt(self, deposit):
        """Generate receipt for a deposit transaction"""
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        
        # Header
        self._draw_header(c, "Deposit")
        
        # Receipt info
        y_pos = self._draw_receipt_info(
            c, 
            receipt_id=f"DEP-{deposit.id}",
            date=deposit.confirmed_at or deposit.created_at,
            status=deposit.status
        )
        
        # User info
        y_pos = self._draw_user_info(c, y_pos, deposit.user)
        
        # Transaction details
        details = {
            "Transaction Type": "Deposit",
            "Cryptocurrency": deposit.crypto_type.upper(),
            "Amount (USD)": f"${deposit.amount:,.2f}",
            "Transaction Hash": deposit.tx_hash[:30] + "..." if deposit.tx_hash and len(deposit.tx_hash) > 30 else (deposit.tx_hash or "Pending"),
            "Created": deposit.created_at.strftime("%Y-%m-%d %H:%M"),
        }
        
        if deposit.confirmed_at:
            details["Confirmed"] = deposit.confirmed_at.strftime("%Y-%m-%d %H:%M")
        if deposit.confirmed_by and hasattr(deposit.confirmed_by, 'full_name'):
            details["Confirmed By"] = deposit.confirmed_by.full_name or "Admin"
        
        y_pos = self._draw_transaction_details(c, y_pos, details)
        
        # Footer
        self._draw_footer(c)
        
        c.save()
        buffer.seek(0)
        return buffer
    
    def generate_withdrawal_receipt(self, withdrawal):
        """Generate receipt for a withdrawal transaction"""
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        
        # Header
        self._draw_header(c, "Withdrawal")
        
        # Receipt info
        y_pos = self._draw_receipt_info(
            c,
            receipt_id=f"WTH-{withdrawal.id}",
            date=withdrawal.processed_at or withdrawal.created_at,
            status=withdrawal.status
        )
        
        # User info
        y_pos = self._draw_user_info(c, y_pos, withdrawal.user)
        
        # Transaction details
        wallet_display = withdrawal.wallet_address
        if len(wallet_display) > 35:
            wallet_display = wallet_display[:18] + "..." + wallet_display[-14:]
        
        details = {
            "Transaction Type": "Withdrawal",
            "Cryptocurrency": withdrawal.crypto_type.upper(),
            "Amount (USD)": f"${withdrawal.amount:,.2f}",
            "Destination Wallet": wallet_display,
            "Transaction Hash": withdrawal.tx_hash[:30] + "..." if withdrawal.tx_hash and len(withdrawal.tx_hash) > 30 else (withdrawal.tx_hash or "Pending"),
            "Requested": withdrawal.created_at.strftime("%Y-%m-%d %H:%M"),
        }
        
        if withdrawal.processed_at:
            details["Processed"] = withdrawal.processed_at.strftime("%Y-%m-%d %H:%M")
        if withdrawal.processed_by and hasattr(withdrawal.processed_by, 'full_name'):
            details["Processed By"] = withdrawal.processed_by.full_name or "Admin"
        
        y_pos = self._draw_transaction_details(c, y_pos, details)
        
        # Footer
        self._draw_footer(c)
        
        c.save()
        buffer.seek(0)
        return buffer
    
    def generate_investment_receipt(self, investment):
        """Generate receipt for an investment purchase"""
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        
        # Header
        self._draw_header(c, "Investment")
        
        # Receipt info
        y_pos = self._draw_receipt_info(
            c,
            receipt_id=f"INV-{investment.id}",
            date=investment.created_at,
            status=investment.status
        )
        
        # User info
        y_pos = self._draw_user_info(c, y_pos, investment.user)
        
        # Transaction details
        details = {
            "Transaction Type": "Investment Purchase",
            "Plan Name": investment.plan.name if investment.plan else "N/A",
            "Investment Amount": f"${investment.amount:,.2f}",
            "Expected ROI": f"{investment.plan.daily_roi}% daily" if investment.plan else "N/A",
            "Duration": f"{investment.plan.duration_days} days" if investment.plan else "N/A",
            "Start Date": investment.start_date.strftime("%Y-%m-%d") if investment.start_date else "N/A",
            "End Date": investment.end_date.strftime("%Y-%m-%d") if investment.end_date else "N/A",
            "Total Expected Profit": f"${investment.expected_profit:,.2f}" if investment.expected_profit else "N/A",
        }
        
        y_pos = self._draw_transaction_details(c, y_pos, details)
        
        # Footer
        self._draw_footer(c)
        
        c.save()
        buffer.seek(0)
        return buffer


# Convenience functions
def generate_deposit_receipt(deposit):
    """Generate deposit receipt PDF"""
    generator = ReceiptGenerator()
    return generator.generate_deposit_receipt(deposit)

def generate_withdrawal_receipt(withdrawal):
    """Generate withdrawal receipt PDF"""
    generator = ReceiptGenerator()
    return generator.generate_withdrawal_receipt(withdrawal)

def generate_investment_receipt(investment):
    """Generate investment receipt PDF"""
    generator = ReceiptGenerator()
    return generator.generate_investment_receipt(investment)
