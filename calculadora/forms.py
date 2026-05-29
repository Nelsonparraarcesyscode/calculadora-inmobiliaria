from django import forms


class CalculadoraForm(forms.Form):
    nombre_completo = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-input', 'placeholder': 'Nombre completo'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input', 'placeholder': 'correo@ejemplo.cl'
        })
    )
    telefono = forms.CharField(
        max_length=20, required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input', 'placeholder': '+56 9 1234 5678'
        })
    )
    valor_propiedad = forms.FloatField(
        min_value=0.01,
        widget=forms.NumberInput(attrs={
            'class': 'form-input', 'placeholder': 'Ej: 3000',
            'step': '0.01', 'x-model.number': 'valorPropiedad',
            'x-on:input': 'calcular()'
        }),
        label="Valor de la Propiedad (UF)"
    )
    pie = forms.FloatField(
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-input', 'placeholder': 'Ej: 600',
            'step': '0.01', 'x-model.number': 'pie',
            'x-on:input': 'calcular()'
        }),
        label="Pie / Enganche (UF)"
    )
    plazo_anios = forms.ChoiceField(
        choices=[(i, f"{i} años") for i in [5, 10, 15, 20, 25, 30]],
        widget=forms.Select(attrs={
            'class': 'form-input', 'x-model.number': 'plazoAnios',
            'x-on:change': 'calcular()'
        }),
        label="Plazo del Crédito"
    )
    tasa_interes_id = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={
            'class': 'form-input', 'x-model': 'tasaInteresId',
            'x-on:change': 'onTasaChange()'
        }),
        label="Tasa de Interés"
    )
    renta_bruta_clp = forms.IntegerField(
        min_value=1,
        widget=forms.TextInput(attrs={
            'class': 'form-input', 'placeholder': 'Ej: 1.500.000',
            'inputmode': 'numeric',
            'x-model': 'rentaBrutaDisplay',
            'x-on:input': 'onRentaInput($event)'
        }),
        label="Renta Bruta Mensual ($CLP)"
    )
    deudas_vigentes_clp = forms.IntegerField(
        min_value=0, required=False, initial=0,
        widget=forms.TextInput(attrs={
            'class': 'form-input', 'placeholder': 'Ej: 200.000',
            'inputmode': 'numeric',
            'x-model': 'deudasVigentesDisplay',
            'x-on:input': 'onDeudasInput($event)'
        }),
        label="Deudas Vigentes Mensuales ($CLP)"
    )

    def __init__(self, *args, tasas=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tasas:
            self.fields['tasa_interes_id'].choices = [
                (t.id, f"{t.nombre} ({t.porcentaje}%)") for t in tasas
            ]

    def clean_renta_bruta_clp(self):
        value = str(self.data.get('renta_bruta_clp', ''))
        value = value.replace('.', '').replace(',', '').strip()
        if not value:
            raise forms.ValidationError('Este campo es obligatorio.')
        try:
            num = int(value)
        except (ValueError, TypeError):
            raise forms.ValidationError('Ingrese un número válido.')
        if num < 1:
            raise forms.ValidationError('Asegúrese de que este valor sea mayor o igual a 1.')
        return num

    def clean_deudas_vigentes_clp(self):
        value = str(self.data.get('deudas_vigentes_clp', ''))
        value = value.replace('.', '').replace(',', '').strip()
        if not value:
            return 0
        try:
            num = int(value)
        except (ValueError, TypeError):
            raise forms.ValidationError('Ingrese un número válido.')
        if num < 0:
            raise forms.ValidationError('Asegúrese de que este valor sea mayor o igual a 0.')
        return num

    def clean(self):
        cleaned_data = super().clean()
        valor_propiedad = cleaned_data.get('valor_propiedad')
        pie = cleaned_data.get('pie')
        if valor_propiedad is not None and pie is not None:
            if pie >= valor_propiedad:
                raise forms.ValidationError(
                    "El pie debe ser menor al valor de la propiedad."
                )
        return cleaned_data
