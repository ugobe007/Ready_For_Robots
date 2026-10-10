/**
 * Shared site header wrapper — delegates to harmonized SiteHeader.
 */
import SiteHeader from './SiteHeader';

export default function SiteTopNav({ session }) {
  return <SiteHeader session={session} />;
}
