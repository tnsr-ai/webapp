"use client";
import AppBar from "@/app/components/AppBar";
import SideDrawer from "@/app/components/SideDrawer";
import ContentListRow from "../../content/contentLists/ContentRowList";

export default function AudioTabs({ params }: { params: { slug: string } }) {
  const content_id = Number(params.slug);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[296px_1fr] grid-rows-[minmax(62px,_90px)_1fr]">
      <div className="lg:col-start-1 lg:col-end-2 lg:row-start-1 lg:row-span-2 hidden lg:block">
        <div className="fixed top-0 h-full">
          <SideDrawer />
        </div>
      </div>
      <div className="sticky top-0 w-[100%] z-50">
        <AppBar />
      </div>
      <div className="mt-5">
        <div className="flex-col max-w-[1500px] flex m-auto mt-5 mb-10">
          <div className="sm:flex sm:items-center">
            <div className="sm:flex-auto">
              <div>
                <ContentListRow content_id={content_id} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
