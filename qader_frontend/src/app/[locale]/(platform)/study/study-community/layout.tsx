import { CommunityNavTabs } from "./_components/CommunityNavTabs";

export default function StudyCommunityLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="container mx-auto max-w-4xl py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">مجتمع الطالب</h1>
        <p className="text-muted-foreground">
          المجتمع الذي يجمعك مع زملائك لتشاركوا التجارب.
        </p>
      </div>

      <CommunityNavTabs />

      <main className="mt-8">{children}</main>
    </div>
  );
}
