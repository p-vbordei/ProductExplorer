import { Injectable, inject } from '@angular/core';
import { Firestore, collection, doc, getDoc, getDocs } from '@angular/fire/firestore';
import { Observable, from, forkJoin } from 'rxjs';
import { map } from 'rxjs/operators';
import { AuthService } from './auth.service';

@Injectable({
  providedIn: 'root'
})
export class CustomerInsightsService {
  firestore: Firestore = inject(Firestore)
  customerInsights$: Observable<any[]>;

  constructor(private authService: AuthService) { }

  get subcollectionNames(): string[] {  
    return ['customerDemographics', 'emotionalJob', 'functionalJob', 'painPoints', 'productComparison', 'socialJob', 'supportingJob', 'usageFrequency', 'usageLocation', 'usageTime', 'useCase'];  // Add more names as needed  
  }

  getDocumentData(userId, id): Observable<any> {
    const reviewInsightRef = doc(this.firestore, 'reviewsInsights', userId, 'investigationCollections', id);
    return from(getDoc(reviewInsightRef)).pipe(
      map(snapshot => {
        if (snapshot.exists()) {
          return snapshot.data();
        } else {
          throw new Error('Document does not exist!');
        }
      })
    );
  }

  getSubcollectionData(subcollectionName: string, userId, id): Observable<any[]> {
    const subcollectionRef = collection(this.firestore, 'reviewsInsights', userId, 'investigationCollections', id, subcollectionName);
    return from(getDocs(subcollectionRef)).pipe(
      map(snapshot => {
        const documents = [];
        snapshot.forEach(doc => {
          documents.push(doc.data());
        });
        return documents;
      })
    );
  }

  getCustomerInsights(id): Observable<any> { 
    const userId = this.authService.userId;
    const subcollectionNames = this.subcollectionNames

    const observables = subcollectionNames.map(name => this.getSubcollectionData(name, userId, id));

    // Add the main document data observable to the start of the observables array
    // observables.unshift(this.getDocumentData(userId, id));

    return forkJoin(observables).pipe(
      map(results => {
        // const mainDocData = results[0];
        const subcollectionsData = results;
        return {
          // mainDocument: mainDocData,
          subcollections: Object.fromEntries(subcollectionNames.map((name, index) => [name, subcollectionsData[index]]))
        };
      })
    );
  }

}
