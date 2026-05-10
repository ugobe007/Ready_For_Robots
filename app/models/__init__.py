# user_profiles must load before CRM FKs that reference it (team_members.user_id).
from app.models.user_profile import UserProfile
from app.models.company import Company
from app.models.contact import Contact
from app.models.signal import Signal
from app.models.score import Score
from app.models.robot import Robot
from app.models.crm import Team, TeamMember, CrmAccount, CrmEngagement
from app.models.lead_rep_feedback import LeadRepFeedback
from app.models.marketplace import (
    BuyerProfile,
    OrganizationAsset,
    OrganizationProfile,
    Rfq,
    RfqInvitation,
    RfqProposal,
    RfqRequirement,
    VendorProfile,
)
from app.models.newsletter_subscriber import NewsletterSubscriber
from app.models.partner_trade_show import PartnerTradeShow
from app.models.scout_chat import ScoutActivation, ScoutMessage, ScoutProfile, ScoutSession
from app.models.waitlist import WaitlistSignup
