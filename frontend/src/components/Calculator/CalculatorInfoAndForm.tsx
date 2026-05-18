import { useEffect } from 'react';
import CalculatorForm from '@/components/Calculator/CalculatorForm';
import CalculatorResult from '@/components/Calculator/CalculatorResult';
import { useCalculator } from '@/hooks/useCalculator';
import { useMedicationById } from '@/hooks/useMedicationsById';

import CalculatorMedicationInfo from '@/components/Calculator/CalculatorMedicationInfo';

function CalculatorInfoAndForm() {
    const { medication, loading: loadingMed, error: errorMed } = useMedicationById();
    const { formData, setFormData, result, loading, error, handleCalculate } = useCalculator();

    useEffect(() => {
        if (medication) {
            setFormData(prev => ({ ...prev, medication_id: medication.id }))
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [medication])

    if (loadingMed) return <p>Carregando medicamento...</p>
    if (errorMed) return <p>{errorMed}</p>
    if (!medication) return null
    return (
        <div className="flex flex-col gap-6 max-w-3xl mx-auto p-4">
            <CalculatorMedicationInfo medication={medication} />

            <CalculatorForm
                formData={formData}
                onChange={setFormData}
                onSubmit={handleCalculate}
                loading={loading}
            />

            {result && <CalculatorResult result={result} warnings={result.warnings} />}
            {error && <p>{error}</p>}
        </div>
    )
}

export default CalculatorInfoAndForm