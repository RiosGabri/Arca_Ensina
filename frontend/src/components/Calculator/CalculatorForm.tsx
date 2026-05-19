import UnitInput from "@/components/ui/unitInput";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import type { CalculatorFormData } from "@/types/calculator";
import { useState } from "react";

import { convertWeight, convertHeight, convertAge } from "@/utils/conversions";

interface CalculatorFormProps {
    formData: CalculatorFormData
    onChange: (data: CalculatorFormData) => void
    onSubmit: (event: React.FormEvent<HTMLFormElement>) => void
    loading: boolean
}


function CalculatorForm(props: CalculatorFormProps) {
    const [weightValue, setWeightValue] = useState<string>("")
    const [heightValue, setHeightValue] = useState<string>("")
    const [weightUnit, setWeightUnit] = useState<"kg" | "g">("kg") //unidade pra o select
    const [heightUnit, setHeightUnit] = useState<"cm" | "m">("cm")

    const [years, setYears] = useState<string>("")
    const [months, setMonths] = useState<string>("")


    function ageChange(newYears: string, newMonths: string) {
        const y = parseInt(newYears) || 0
        const m = parseInt(newMonths) || 0
        const days = convertAge(y, m)
        props.onChange({ ...props.formData, age_days: days })
    }

    return (
        <form onSubmit={props.onSubmit}>
            <div className="flex flex-col gap-3">
                <UnitInput
                    label="Peso"
                    value={weightValue ?? ""}
                    placeholder="Digite o peso"
                    onChange={(value) => {
                        setWeightValue(value)
                        const parsed = parseFloat(value)
                        if (!isNaN(parsed)) {
                            props.onChange({ ...props.formData, weight: parsed })
                        }
                    }}
                    units={["kg", "g"]}
                    unit={weightUnit}
                    onUnitChange={(newUnit) => {
                        const unit = newUnit as "kg" | "g"
                        if (props.formData.weight !== null) {
                            props.onChange({
                                ...props.formData,
                                weight: convertWeight(props.formData.weight, unit)
                            })
                        }
                        setWeightUnit(unit)
                    }}

                />
                <UnitInput
                    label="Altura"
                    value={heightValue ?? ""}
                    placeholder="Digite a altura"
                    onChange={(value) => {
                        setHeightValue(value)
                        const parsed = parseFloat(value)
                        if (!isNaN(parsed)) {
                            props.onChange({ ...props.formData, height: parsed })
                        }
                    }}
                    unit={heightUnit}
                    units={["cm", "m"]}
                    onUnitChange={(newUnit) => {
                        const unit = newUnit as "cm" | "m"
                        if (props.formData.height !== null) {
                            props.onChange({
                                ...props.formData,
                                height: convertHeight(props.formData.height, unit)
                            })
                        }
                        setHeightUnit(unit)
                    }}
                />
                <label htmlFor="idade" className="text-sm font-medium text-foreground">Idade</label>
                <Input
                    type="number"
                    min={0}
                    placeholder="Quantos anos?"
                    value={years}
                    onChange={(e) => {
                        setYears(e.target.value)
                        ageChange(e.target.value, months)
                    }}
                />
                <Input
                    placeholder="Quantos meses?"
                    type="number"
                    min={0}
                    max={11}
                    value={months}
                    onChange={(e) => {
                        setMonths(e.target.value)
                        ageChange(years, e.target.value)
                    }}
                />

                <Button type="submit" variant="default" className="mt-2">
                    {props.loading ? "Calculando..." : "Calcular"}
                </Button>
            </div>

        </form>
    );
}
export default CalculatorForm;