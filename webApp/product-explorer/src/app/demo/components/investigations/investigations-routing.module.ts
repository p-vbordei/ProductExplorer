import { NgModule } from '@angular/core';
import { RouterModule } from '@angular/router';
import { InvestigationsComponent } from './investigations.component';

@NgModule({
    imports: [RouterModule.forChild([
        { path: '', component: InvestigationsComponent }
    ])],
    exports: [RouterModule]
})
export class InvestigationsRoutingModule { }
