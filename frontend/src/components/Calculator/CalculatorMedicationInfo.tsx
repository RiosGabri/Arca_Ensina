interface Medication {
    name: string;
    category: string;
    description: string;
}

function CalculatorMedicationInfo({ medication}: { medication: Medication}) {
    return (
        <div>
            <h1 className="text-2xl font-semibold text-black">{medication.name}</h1>
            <p className="text-lg font-semibold text-blue-500">{medication.category}</p>
            <p className="text-md mt-2">{medication.description}</p>
        </div>
    )
}

export default CalculatorMedicationInfo;