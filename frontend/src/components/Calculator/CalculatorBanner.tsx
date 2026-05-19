import MedicationBadge from "../Medications/MedicationBadge";

function CalculatorBanner() {
    return (
        <div className="flex flex-col gap-3 items-center bg-gray-300 px-12 py-14 rounded-lg h-full justify-center">
            <section className="flex">
                <MedicationBadge name="pill" size={32}/>
                <MedicationBadge name="tablets" size={32} />
                <MedicationBadge name="pills-bottle" size={32} />
                <MedicationBadge name="syringe" size={32} />
            </section>
            <section>
                <p className="bg-arca-blue-600 text-white p-2 rounded-full text-center">Calculadora de Medicamentos</p>
            </section>
        </div>
    );
}

export default CalculatorBanner;