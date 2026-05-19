import { Pill } from "lucide-react";
import { PillBottle } from "lucide-react";
import { Tablets } from "lucide-react";
import { Syringe } from "lucide-react";
import { ShieldPlus } from "lucide-react";
import { HeartPulse } from "lucide-react";
import { Bandage } from "lucide-react";
import { BriefcaseMedical } from "lucide-react";

function MedicationBadge({ name, size = 16 }: { name: string; size?: number }) {
    return (
        <div className="bg-arca-blue-600 text-white text-sm font-medium mr-2  rounded-full flex items-center" style={{ padding: `${size / 4}px`}}>
            {name === "pill" ? (
                <Pill size={size} />
            ) : name === "tablets" ? (
                <Tablets size={size} />
            ) : name === "pills-bottle" ? (
                <PillBottle size={size} />
            ) : name === "syringe" ? (
                <Syringe size={size} />
            ) : name === "shield-plus" ? (
                <ShieldPlus size={size} />
            ) : name === "heart-pulse" ? (
                <HeartPulse size={size} />
            ) : name === "bandage" ? (
                <Bandage size={size} />
            ) : name === "briefcase-medical" ? (
                <BriefcaseMedical size={size} />
            ) : null}
        </div>
    );
}

export default MedicationBadge;