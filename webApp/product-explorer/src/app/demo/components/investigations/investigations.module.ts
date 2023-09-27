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
import { ReactiveFormsModule } from '@angular/forms';
import { MessageService } from 'primeng/api';
import { ToastModule } from 'primeng/toast';


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
    InputTextModule,
    ReactiveFormsModule,
    ToastModule
],
declarations: [InvestigationsComponent],
providers: [MessageService]
})
export class InvestigationsModule { }
