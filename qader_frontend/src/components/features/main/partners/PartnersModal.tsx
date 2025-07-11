"use client";

import React, { useState } from "react";
import Image from "next/image";
import { PaperAirplaneIcon, XMarkIcon } from "@heroicons/react/24/solid";
import type { PartnerCategory } from "@/types/api/content.types";

interface PartnersModalProps {
  partnerCategories: PartnerCategory[];
  show: boolean;
  onClose: () => void;
}

const PartnersModal: React.FC<PartnersModalProps> = ({
  partnerCategories,
  show,
  onClose,
}) => {
  const [selectedPartners, setSelectedPartners] = useState<
    Record<number, boolean>
  >({});

  const handleCheckboxChange = (partnerId: number) => {
    setSelectedPartners((prev) => ({ ...prev, [partnerId]: !prev[partnerId] }));
  };

  const isAnySelected = Object.values(selectedPartners).some((v) => v);

  const handleSubmit = () => {
    const selected = partnerCategories.filter((p) => selectedPartners[p.id]);
    const links = selected.map((p) => p.google_form_link);
    // For simplicity, we open the first selected link.
    // A more complex app might show a list of links.
    if (links.length > 0) {
      window.open(links[0], "_blank");
    }
    onClose();
  };

  if (!show) return null;

  return (
    <div
      className="fixed inset-0 bg-black/50 flex justify-center items-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-white dark:bg-[#0B1739] p-6 md:p-10 rounded-xl shadow-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto relative"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-500 hover:text-gray-800 dark:hover:text-white"
        >
          <XMarkIcon className="w-6 h-6" />
        </button>
        <div className="flex flex-col justify-center items-center gap-4">
          <h2 className="text-3xl font-bold">اختر نوع الشراكة</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full">
            {partnerCategories.map((partner, index) => {
              // --- START OF FIX ---
              const defaultIcon = `/images/partner${index + 1}.png`;
              const iconSrc = partner.icon_image ?? defaultIcon;
              // --- END OF FIX ---

              return (
                <label
                  key={partner.id}
                  className={`bg-[#e7f1fe] dark:bg-transparent rounded-2xl border p-6 cursor-pointer transition-all ${
                    selectedPartners[partner.id]
                      ? "border-blue-500 ring-2 ring-blue-500"
                      : "border-[#cfe4fc]"
                  }`}
                >
                  <div className="flex justify-between items-center mb-4">
                    <Image
                      src={iconSrc}
                      width={40}
                      height={40}
                      alt={partner.name}
                    />
                    <input
                      type="checkbox"
                      checked={!!selectedPartners[partner.id]}
                      onChange={() => handleCheckboxChange(partner.id)}
                      className="form-checkbox h-5 w-5 text-blue-600 rounded-full border-gray-300 focus:ring-blue-500"
                    />
                  </div>
                  <div className="text-center mt-4">
                    <p className="text-xl font-bold">{partner.name}</p>
                    <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                      {partner.description}
                    </p>
                  </div>
                </label>
              );
            })}
          </div>

          <button
            className={`flex justify-center items-center gap-2 mt-6 py-3 px-8 w-full max-w-sm rounded-lg text-white font-semibold transition-all ${
              !isAnySelected
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-[#074182] hover:bg-[#053061]"
            }`}
            disabled={!isAnySelected}
            onClick={handleSubmit}
          >
            <PaperAirplaneIcon className="w-5 h-5" />
            تقديم الطلب
          </button>
        </div>
      </div>
    </div>
  );
};

export default PartnersModal;
