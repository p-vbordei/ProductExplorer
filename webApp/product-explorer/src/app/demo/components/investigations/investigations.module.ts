import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChartModule } from 'primeng/chart';
import { MenuModule } from 'primeng/menu';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { StyleClassModule } from 'primeng/styleclass';
import { PanelMenuModule } from 'primeng/panelmenu';
import { ProgressBarModule } from 'primeng/progressbar';
import { TagModule } from 'primeng/tag';
import { InputTextareaModule } from "primeng/inputtextarea";
import { InvestigationsComponent } from './investigations.component';
import { InvestigationsRoutingModule } from './investigations-routing.module';
import { InputTextModule } from "primeng/inputtext";

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    ChartModule,
    MenuModule,
    TableModule,
    StyleClassModule,
    PanelMenuModule,
    ButtonModule,
    ProgressBarModule,
    TagModule,
    InvestigationsRoutingModule,
    InputTextareaModule,
    InputTextModule
],
declarations: [InvestigationsComponent]
})
export class InvestigationsModule { }
