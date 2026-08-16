# user_profiles must load before CRM FKs that reference it (team_members.user_id).
from app.models.user_profile import UserProfile
from app.models.company import Company
from app.models.contact import Contact
from app.models.signal import Signal
from app.models.score import Score
from app.models.robot import Robot
from app.models.robot_catalog import Manufacturer, RobotConfiguration, RobotFamily, RobotModel
from app.models.robot_intelligence import (
    EvidenceClaim,
    RobotAnalysis,
    RobotCapability,
    RobotProfileVersion,
)
from app.models.source import Source
from app.models.facility import Facility
from app.models.primitive import Primitive
from app.models.work_graph import WorkMatchRecord, WorkUnitRecord
from app.models.robot_directed_discovery import (
    AutomationInterpretation,
    JobEvidence,
    RobotCapabilityProfile,
    RobotJob,
    RobotJobMatch,
    WorkClaim,
)
from app.models.deployment_evidence import (
    DeploymentEvent,
    DeploymentEvidence,
    DeploymentMetric,
    DeploymentSource,
)
from app.models.vendor_news import VendorNewsItem
from app.models.robot_company import RobotCompany
from app.models.crm import Team, TeamMember, CrmAccount, CrmEngagement
from app.models.lead_rep_feedback import LeadRepFeedback
from app.models.marketplace import (
    BuyerProfile,
    MarketplaceCommercialDocument,
    MarketplaceIntegrationConnection,
    MarketplacePartnerApiKey,
    OrganizationAsset,
    OrganizationProfile,
    Rfq,
    RfqInvitation,
    RfqProposal,
    RfqRequirement,
    RfqScheduleEvent,
    VendorProfile,
)
from app.models.newsletter_subscriber import NewsletterSubscriber
from app.models.partner_trade_show import PartnerTradeShow
from app.models.lead_research import LeadResearchUpdate, UserNotification
from app.models.outreach import OutreachMessage, OutreachReply
from app.models.sales_agent import SalesAgentAction, SalesMessage, SalesOpportunity
from app.models.sales_learning import SalesExperienceEvent
from app.models.supply_outreach import SupplyOutreachMessage, SupplyOutreachReply
from app.models.calendar import CalendarEvent
from app.models.scout_chat import ScoutActivation, ScoutMessage, ScoutProfile, ScoutSession
from app.models.waitlist import WaitlistSignup
from app.models.robot_buyer_lead import RobotBuyerLead
from app.models.site_analytics_event import SiteAnalyticsEvent
from app.models.humanoid_report_snapshot import HumanoidReportSnapshot
from app.models.special_project import (
    SpecialProject,
    SpecialProjectTarget,
    SpecialProjectUpdate,
)
