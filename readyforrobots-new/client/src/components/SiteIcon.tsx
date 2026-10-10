/**
 * Lookup a catalog icon by id. Pages should import this, not copy maps.
 */
import PixelIcon from "@/components/PixelIcon";
import {
  SITE_ICON_FILL,
  iconForWorkClass,
  siteIconMap,
  type SiteIconId,
} from "@/lib/siteIcons";

type Props = {
  id: SiteIconId;
  scale?: number;
  fill?: string;
  background?: string;
  label?: string;
  className?: string;
};

export default function SiteIcon({
  id,
  scale = 1,
  fill = SITE_ICON_FILL,
  background = "transparent",
  label,
  className = "",
}: Props) {
  return (
    <span aria-hidden={label ? undefined : true} className="inline-flex">
      <PixelIcon
        map={siteIconMap(id)}
        scale={scale}
        fill={fill}
        background={background}
        label={label}
        className={className}
      />
    </span>
  );
}

export function WorkClassIcon({
  classId,
  scale = 1,
}: {
  classId: string;
  scale?: number;
}) {
  const id = iconForWorkClass(classId);
  if (!id) return null;
  return <SiteIcon id={id} scale={scale} />;
}

export type { SiteIconId };
